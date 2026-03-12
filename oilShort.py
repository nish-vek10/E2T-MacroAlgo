# ==== OIL SHORT ==== #

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import MetaTrader5 as mt5

import config  # noqa: F401  — initialises logging
from baseClass import MT5Trader, MT5ConnectionParams
from config import (
    MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER,
    RISK_PERCENT, MAGIC_NUMBER, DEVIATION, RETRIES, RETRY_SLEEP_S,
)

log = logging.getLogger(__name__)

ASSETS = [
    ("XBRUSD", mt5.ORDER_TYPE_SELL, 20),  # Brent Oil
    ("XTIUSD", mt5.ORDER_TYPE_SELL, 20),  # Crude Oil (WTI)
]


def _trade(trader: MT5Trader, symbol: str, order_type: int, sl: int) -> bool:
    if trader.has_open_position(symbol):
        log.warning("%s: Position already open — skipping.", symbol)
        return False
    lot = trader.calculate_lot_size(symbol, sl, RISK_PERCENT)
    if lot <= 0:
        return False
    return trader.place_order(symbol, order_type, lot, sl, comment="OilShortAuto")


def main():
    conn = MT5ConnectionParams(
        path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER,
    )
    with MT5Trader(
        conn=conn, retries=RETRIES, retry_sleep_s=RETRY_SLEEP_S,
        magic=MAGIC_NUMBER, deviation=DEVIATION,
    ) as trader:
        with ThreadPoolExecutor(max_workers=len(ASSETS)) as pool:
            futures = {
                pool.submit(_trade, trader, sym, ot, sl): sym
                for sym, ot, sl in ASSETS
            }
            for fut in as_completed(futures):
                exc = fut.exception()
                if exc:
                    log.error("%s: Unhandled exception: %s", futures[fut], exc)


if __name__ == "__main__":
    main()
