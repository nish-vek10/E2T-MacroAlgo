# E2T-Macro — MT5 One-Click Macro Trader

Python scripts for instant multi-symbol market execution via Stream Deck buttons.
Each script connects to MetaTrader 5, calculates position sizes to a fixed risk %, and fires all orders **in parallel** for maximum speed during news events.

---

## Project Structure

```
E2T-Macro/
├── config.py          ← ALL credentials & settings live here (gitignored)
├── baseClass.py       ← Core MT5Trader class — connection, sizing, execution
│
├── riskOn.py          ← Long equities, short JPY, long EUR/USD
├── riskOff.py         ← Short equities, long JPY/CHF, long Gold, short EUR/USD
├── oilLong.py         ← Long Brent + WTI
├── oilShort.py        ← Short Brent + WTI
│
├── closeAll.py        ← Close all EA positions (parallel)
├── closePartial.py    ← Close 50% of all EA positions (parallel)
│
├── requirements.txt
├── logs/              ← Auto-created; all trade activity logged here
└── old/               ← Legacy files (ignored)
```

---

## Prerequisites

- Windows 10 / 11
- Python 3.10+ (64-bit)
- MetaTrader 5 terminal installed and logged in
- Elgato Stream Deck (optional — scripts can also be run directly)

---

## Setup

**1. Clone / copy the project folder**

**2. Create and activate a virtual environment**
```bat
cd C:\Users\anish\PycharmProjects\E2T-Macro
python -m venv .venv
.venv\Scripts\activate
```

**3. Install dependencies**
```bat
pip install -r requirements.txt
```

**4. Configure `config.py`**
Open `config.py` and fill in your account details and preferred settings (see section below).
**Never commit this file to git** — add it to `.gitignore`.

---

## Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `MT5_PATH` | `C:\MT5\xInterns\terminal64.exe` | Full path to your MT5 `terminal64.exe` |
| `MT5_LOGIN` | `52421640` | MT5 account number |
| `MT5_PASSWORD` | `"..."` | MT5 account password |
| `MT5_SERVER` | `"ICMarketsSC-Demo"` | MT5 broker server name |
| `RISK_PERCENT` | `1.0` | % of account balance risked per trade (1.0 = 1%) |
| `MAGIC_NUMBER` | `123456` | EA identifier — used to tag and filter EA-opened positions |
| `DEVIATION` | `250` | Max slippage in points — kept high for news event fills |
| `CLOSE_MAGIC_ONLY` | `True` | `True` = close scripts only touch EA positions; `False` = close everything |
| `RETRIES` | `2` | MT5 connection attempts before aborting |
| `RETRY_SLEEP_S` | `0.3` | Seconds between connection retries |

### Multiple users (interns)
Each user should have their own `config.py` with their own credentials.
The rest of the codebase is identical — only `config.py` changes per machine.

---

## Scripts

### Strategy Scripts

| Script | Direction | Symbols |
|---|---|---|
| `riskOn.py` | Risk-On | USTEC ↑, US500 ↑, DE40 ↑, UK100 ↑, USDJPY ↓, EURUSD ↑ |
| `riskOff.py` | Risk-Off | USTEC ↓, US500 ↓, DE40 ↓, USDJPY ↑, CHFJPY ↑, XAUUSD ↑, EURUSD ↓ |
| `oilLong.py` | Oil Long | XBRUSD ↑, XTIUSD ↑ |
| `oilShort.py` | Oil Short | XBRUSD ↓, XTIUSD ↓ |

All strategy scripts:
- Check for an existing EA position before placing (prevents accidental double-entry)
- Calculate lot size using the risk % set in `config.py`
- Fire all orders **simultaneously** using threads

### Management Scripts

| Script | Action |
|---|---|
| `closeAll.py` | Closes all EA positions in parallel |
| `closePartial.py` | Closes 50% of each EA position in parallel |

---

## Stream Deck Setup

Each Stream Deck button runs a `.bat` file. The `/high` flag raises the process priority so Windows doesn't deprioritise the script during a busy market event.

**Template `.bat` file:**
```bat
@echo off
cd /d C:\Users\anish\PycharmProjects\E2T-Macro
start /high "" .venv\Scripts\pythonw.exe riskOn.py
```

Use `pythonw.exe` (not `python.exe`) to suppress the console window.
Use `python.exe` instead if you want to see the terminal output while testing.

**Suggested button layout:**

| Button | `.bat` target |
|---|---|
| RISK ON | `riskOn.py` |
| RISK OFF | `riskOff.py` |
| OIL LONG | `oilLong.py` |
| OIL SHORT | `oilShort.py` |
| CLOSE ALL | `closeAll.py` |
| CLOSE 50% | `closePartial.py` |

---

## Logging

All trade activity is written to **`logs/trades.log`** (auto-created on first run).
The same output is also printed to the console if running with `python.exe`.

Log format:
```
14:32:01.042 [INFO] [OK] USTEC: Filled 0.020 lot @ 19845.50000  SL=18845.50000
14:32:01.051 [INFO] [OK] US500: Filled 0.030 lot @ 5520.25000  SL=5470.25000
14:32:01.053 [WARNING] EURUSD: Position already open — skipping.
```

---

## Key Notes

### Risk calculation
`RISK_PERCENT = 1.0` means **1% of account balance** per trade.
The formula is: `risk_amount = (RISK_PERCENT / 100) × balance`
So with a $10,000 account and `RISK_PERCENT = 1.0`: risk per trade = **$100**.

### Magic number
All positions opened by these scripts are tagged with `MAGIC_NUMBER = 123456`.
`closeAll.py` and `closePartial.py` only touch positions with this tag by default,
so manually opened trades are never affected. Set `CLOSE_MAGIC_ONLY = False` in
`config.py` to close all positions regardless.

### Filling mode
The broker's supported filling mode (FOK / IOC / Return) is auto-detected per symbol
from `symbol_info.filling_mode` — no manual configuration needed.

### Slippage (`DEVIATION = 250`)
250 points of slippage tolerance is intentionally high for news trading.
Tighten this in `config.py` if you want stricter fill control outside of news windows.

---

## .gitignore

Add the following to your `.gitignore` to prevent credentials from being committed:

```
config.py
logs/
__pycache__/
.venv/
*.pyc
```
