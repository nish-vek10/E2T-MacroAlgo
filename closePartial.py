# ==== PARTIAL CLOSE (50%) ==== #

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import MetaTrader5 as mt5

import config  # noqa: F401  — initialises logging
from baseClass import MT5Trader, MT5ConnectionParams
from config import (
    MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER,
    MAGIC_NUMBER, DEVIATION, RETRIES, RETRY_SLEEP_S,
)

log = logging.getLogger(__name__)


def main():
    conn = MT5ConnectionParams(
        path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER,
    )
    with MT5Trader(
        conn=conn, retries=RETRIES, retry_sleep_s=RETRY_SLEEP_S,
        magic=MAGIC_NUMBER, deviation=DEVIATION,
    ) as trader:
        all_positions = mt5.positions_get()
        if not all_positions:
            log.info("No open positions.")
            return

        # Only close positions opened by this EA
        positions = [p for p in all_positions if p.magic == MAGIC_NUMBER]
        if not positions:
            log.info("No positions matching magic number %d.", MAGIC_NUMBER)
            return

        with ThreadPoolExecutor(max_workers=len(positions)) as pool:
            futures = {
                pool.submit(trader.close_half_position, pos): pos.symbol
                for pos in positions
            }
            for fut in as_completed(futures):
                exc = fut.exception()
                if exc:
                    log.error("%s: Unhandled exception: %s", futures[fut], exc)


if __name__ == "__main__":
    main()
