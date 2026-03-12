# ==== CLOSE ALL ==== #

from __future__ import annotations

import logging

import config  # noqa: F401  — initialises logging
from baseClass import MT5Trader, MT5ConnectionParams
from config import (
    MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER,
    MAGIC_NUMBER, DEVIATION, RETRIES, RETRY_SLEEP_S, CLOSE_MAGIC_ONLY,
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
        trader.close_all_positions(magic_only=CLOSE_MAGIC_ONLY)


if __name__ == "__main__":
    main()
