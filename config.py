# config.py
# Central configuration for all E2T-Macro trading scripts.
# Add this file to .gitignore — it contains live credentials.

import logging
import os

# ── MT5 Terminal ──────────────────────────────────────────────────────────────
MT5_PATH     = r"C:\MT5\xInterns\terminal64.exe"
MT5_LOGIN    = 52421640
MT5_PASSWORD = "M3Bgywv9$n8mr1"
MT5_SERVER   = "ICMarketsSC-Demo"

# ── Trading Settings ──────────────────────────────────────────────────────────
RISK_PERCENT     = 1.0          # % of account balance to risk per trade  (1.0 = 1%)
MAGIC_NUMBER     = 123456       # EA identifier — used to filter which positions to close
DEVIATION        = 250          # Max slippage in points (kept high for news event fills)
CLOSE_MAGIC_ONLY = True         # True = only close EA-opened positions; False = close all

# ── Connection ────────────────────────────────────────────────────────────────
RETRIES       = 2
RETRY_SLEEP_S = 0.3

# ── Logging ───────────────────────────────────────────────────────────────────
_log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_log_dir, "trades.log"), encoding="utf-8"),
    ],
)
