#####  P-A-R-T-I-A-L   C-L-O-S-E  (50%)  #####

from baseClass import MT5Trader, MT5ConnectionParams
import MetaTrader5 as mt5

# --- OPTIONAL: specify a particular terminal + account to use ---
MT5_PATH     = r"C:\MT5\xInterns\terminal64.exe"
MT5_LOGIN    = 52421640
MT5_PASSWORD = "M3Bgywv9$n8mr1"
MT5_SERVER   = "ICMarketsSC-Demo"

# Initialize trader
conn = MT5ConnectionParams(
    path=MT5_PATH,
    login=MT5_LOGIN,
    password=MT5_PASSWORD,
    server=MT5_SERVER,
)
trader = MT5Trader(conn=conn)

# Get all open positions
positions = mt5.positions_get()

if positions is None or len(positions) == 0:
    print("[INFO] No open positions found.")
else:
    for position in positions:
        trader.close_half_position(position)

# Shutdown
trader.shutdown()
