# baseClass.py

from __future__ import annotations

import math
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import MetaTrader5 as mt5

log = logging.getLogger(__name__)


@dataclass
class MT5ConnectionParams:
    """
    Parameters to initialize a specific MT5 terminal + account.
    path: full path to terminal64.exe (for a specific/portable install).
    login/password/server: account credentials.
    All fields are optional; MT5 uses the default running session if omitted.
    """
    path:     Optional[str] = None
    login:    Optional[int] = None
    password: Optional[str] = None
    server:   Optional[str] = None


class MT5Trader:

    def __init__(
        self,
        conn:          Optional[MT5ConnectionParams] = None,
        retries:       int   = 2,
        retry_sleep_s: float = 0.3,
        magic:         int   = 123456,
        deviation:     int   = 250,
    ):
        self.magic_number = magic
        self.deviation    = deviation
        self._connected   = False
        self._connect(conn, retries=retries, retry_sleep_s=retry_sleep_s)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> MT5Trader:
        return self

    def __exit__(self, *_) -> bool:
        self.shutdown()
        return False  # do not suppress exceptions

    # ── Connection ────────────────────────────────────────────────────────────

    def _connect(self, conn: Optional[MT5ConnectionParams], retries: int, retry_sleep_s: float):
        kwargs: dict = {}
        if conn:
            if conn.path:     kwargs["path"]     = conn.path
            if conn.login:    kwargs["login"]    = int(conn.login)
            if conn.password: kwargs["password"] = conn.password
            if conn.server:   kwargs["server"]   = conn.server

        for attempt in range(1, max(1, retries) + 1):
            ok = mt5.initialize(**kwargs) if kwargs else mt5.initialize()
            if ok:
                self._connected = True
                time.sleep(0.05)      # minimal sanity wait
                mt5.account_info()    # connection ping
                return
            log.warning("[INIT] Attempt %d/%d failed: %s", attempt, retries, mt5.last_error())
            time.sleep(retry_sleep_s)

        raise SystemExit(f"MT5 initialization failed: {mt5.last_error()}")

    def shutdown(self):
        """Shut down the MT5 connection."""
        if self._connected:
            mt5.shutdown()
            self._connected = False

    # ── Tick / symbol helpers ─────────────────────────────────────────────────

    def get_tick_info(self, symbol: str):
        """Return (tick, symbol_info), or (None, None) on failure."""
        info = mt5.symbol_info(symbol)
        if info is None:
            log.error("%s: No symbol_info.", symbol)
            return None, None
        if not info.visible:
            mt5.symbol_select(symbol, True)
            info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            log.error("%s: No tick data.", symbol)
            return None, None
        return tick, info

    def _wait_fresh_tick(self, symbol: str, timeout_ms: int = 300):
        """
        Poll for a fresh tick up to timeout_ms milliseconds.
        Falls back to the latest available tick on timeout.
        Polling every 5 ms keeps latency tight for news execution.
        """
        start     = time.time()
        last_time = 0
        while (time.time() - start) * 1000 < timeout_ms:
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.time_msc and tick.time_msc != last_time:
                return tick
            last_time = tick.time_msc if tick else last_time
            time.sleep(0.005)  # 5 ms
        return mt5.symbol_info_tick(symbol)

    def _get_filling_mode(self, symbol_info) -> int:
        """
        Auto-detect the broker's supported order filling mode for this symbol.
        filling_mode bitmask: bit-0 = FOK, bit-1 = IOC, else Return/Book.
        """
        filling = getattr(symbol_info, "filling_mode", 0)
        if filling & 1:
            return mt5.ORDER_FILLING_FOK
        if filling & 2:
            return mt5.ORDER_FILLING_IOC
        return mt5.ORDER_FILLING_RETURN

    def adjust_sl_to_broker_min(self, symbol_info, sl_points: int) -> int:
        """Clamp SL to the broker's minimum stop distance."""
        min_sl = getattr(symbol_info, "trade_stops_level", 0) or 0
        if sl_points < min_sl:
            log.warning(
                "%s: SL %d below broker minimum %d — adjusting.",
                symbol_info.name, sl_points, min_sl,
            )
            return int(min_sl)
        return int(sl_points)

    def has_open_position(self, symbol: str) -> bool:
        """Return True if this EA already has an open position on the given symbol."""
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return False
        return any(p.magic == self.magic_number for p in positions)

    # ── Lot sizing ────────────────────────────────────────────────────────────

    def calculate_lot_size(self, symbol: str, sl_points: int, risk_percent: float) -> float:
        """
        Calculate position size from account balance, risk percentage, and SL size.

        risk_percent: percentage value — e.g. 1.0 means 1% of account balance.
        Returns 0.0 on any error or if the calculated lot falls below the broker minimum.
        """
        account_info = mt5.account_info()
        if account_info is None:
            log.error("Unable to retrieve account info.")
            return 0.0

        balance     = float(account_info.balance)
        risk_amount = (float(risk_percent) / 100.0) * balance

        tick, symbol_info = self.get_tick_info(symbol)
        if not tick or not symbol_info:
            return 0.0

        sl_points     = self.adjust_sl_to_broker_min(symbol_info, sl_points)
        contract_size = getattr(symbol_info, "trade_contract_size", 0) or 0
        tick_value    = getattr(symbol_info, "trade_tick_value",    0) or 0
        point         = float(symbol_info.point or 0.0)

        if contract_size == 0 or tick_value == 0 or point <= 0:
            log.error("%s: Invalid contract or tick value.", symbol)
            return 0.0

        sl_price_range = float(sl_points) * point
        if sl_price_range <= 0:
            log.error("%s: Invalid SL or contract parameters.", symbol)
            return 0.0

        sl_value_per_lot = sl_price_range * (tick_value / point)
        if sl_value_per_lot == 0:
            log.error("%s: Division by zero in SL value per lot.", symbol)
            return 0.0

        raw_lot  = risk_amount / sl_value_per_lot
        min_lot  = float(symbol_info.volume_min)
        max_lot  = float(symbol_info.volume_max)
        lot_step = float(symbol_info.volume_step)

        if lot_step <= 0 or min_lot <= 0 or max_lot <= 0:
            log.error("%s: Invalid lot constraints.", symbol)
            return 0.0

        lot = max(min_lot, min(raw_lot, max_lot))
        lot = math.floor(lot / lot_step) * lot_step  # floor to avoid over-risk
        lot = round(lot, 3)

        if lot < min_lot:
            log.warning("%s: Calculated lot %.3f below minimum %.3f — skipping.", symbol, lot, min_lot)
            return 0.0

        return lot

    # ── Order execution ───────────────────────────────────────────────────────

    def place_order(
        self,
        symbol:     str,
        order_type: int,
        lot:        float,
        sl_points:  int,
        comment:    str = "AutoTrade",
    ) -> bool:
        """
        Place a market order with SL.
        Waits for the freshest available tick before sending to maximise
        price accuracy during fast-moving news events.
        Returns True on a confirmed fill.
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            log.error("%s: No symbol_info.", symbol)
            return False
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)
            symbol_info = mt5.symbol_info(symbol)

        tick = self._wait_fresh_tick(symbol)
        if not tick:
            log.error("%s: No tick data.", symbol)
            return False

        point = float(symbol_info.point or 0.0)
        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid

        # Enforce broker minimum SL
        min_sl = getattr(symbol_info, "trade_stops_level", 0) or 0
        if sl_points < min_sl:
            log.warning("%s: SL %d below minimum %d — adjusting.", symbol, sl_points, min_sl)
            sl_points = int(min_sl)

        sl_price = (
            price - sl_points * point if order_type == mt5.ORDER_TYPE_BUY
            else price + sl_points * point
        )

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       float(lot),
            "type":         int(order_type),
            "price":        float(price),
            "deviation":    self.deviation,
            "sl":           float(sl_price),
            "magic":        int(self.magic_number),
            "comment":      str(comment),
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol_info),
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log.info(
                "[OK] %s: Filled %.3f lot @ %.5f  SL=%.5f",
                symbol, lot, result.price, sl_price,
            )
            return True

        log.error(
            "[FAIL] %s: retcode=%s | %s",
            symbol, getattr(result, "retcode", None), result,
        )
        return False

    # ── Position management ───────────────────────────────────────────────────

    def _close_single_position(self, pos) -> bool:
        """Close one position fully. Called per-thread in close_all_positions."""
        symbol     = pos.symbol
        ticket     = pos.ticket
        volume     = float(pos.volume)
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            log.error("%s: No tick data.", symbol)
            return False

        price       = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        symbol_info = mt5.symbol_info(symbol)
        filling     = self._get_filling_mode(symbol_info) if symbol_info else mt5.ORDER_FILLING_IOC

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       float(volume),
            "type":         int(order_type),
            "position":     int(ticket),
            "price":        float(price),
            "deviation":    self.deviation,
            "magic":        int(self.magic_number),
            "comment":      "CloseAll",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log.info("[OK] Closed %s #%d @ %.5f", symbol, ticket, price)
            return True

        log.error("[FAIL] %s #%d retcode=%s", symbol, ticket, getattr(result, "retcode", None))
        return False

    def close_all_positions(self, magic_only: bool = True) -> None:
        """
        Close all open positions in parallel for maximum speed.
        magic_only=True (default): only close positions opened by this EA.
        magic_only=False: close every open position on the account.
        """
        positions = mt5.positions_get()
        if not positions:
            log.info("No open positions.")
            return

        if magic_only:
            positions = [p for p in positions if p.magic == self.magic_number]
            if not positions:
                log.info("No positions matching magic number %d.", self.magic_number)
                return

        with ThreadPoolExecutor(max_workers=len(positions)) as pool:
            futures = {
                pool.submit(self._close_single_position, pos): pos.symbol
                for pos in positions
            }
            for fut in as_completed(futures):
                exc = fut.exception()
                if exc:
                    log.error("%s: Unhandled exception during close: %s", futures[fut], exc)

    def close_half_position(self, position) -> None:
        """Close 50% of the given position."""
        symbol      = position.symbol
        ticket      = position.ticket
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            log.error("%s: No symbol info.", symbol)
            return

        half_vol = float(position.volume) / 2.0
        min_lot  = float(symbol_info.volume_min)
        lot_step = float(symbol_info.volume_step)

        rounded_vol = math.floor(half_vol / lot_step) * lot_step
        rounded_vol = round(rounded_vol, 3)

        if rounded_vol < min_lot:
            log.warning(
                "%s: 50%% volume %.3f < min lot %.3f — skipping.",
                symbol, rounded_vol, min_lot,
            )
            return

        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            log.error("%s: No tick data.", symbol)
            return

        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       float(rounded_vol),
            "type":         int(order_type),
            "position":     int(ticket),
            "price":        float(price),
            "deviation":    self.deviation,
            "magic":        int(self.magic_number),
            "comment":      "PartialClose50",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol_info),
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log.info("Closed 50%% of %s #%d", symbol, ticket)
        else:
            log.error(
                "Failed partial close %s #%d (retcode=%s)",
                symbol, ticket, getattr(result, "retcode", None),
            )
