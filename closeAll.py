#####   C-L-O-S-E  A-L-L   #####

from baseClass import MT5Trader, MT5ConnectionParams

# --- OPTIONAL: specify a particular terminal + account to use ---
MT5_PATH     = r"C:\MT5\52474875\terminal64.exe"
MT5_LOGIN    = 52474875
MT5_PASSWORD = "W7J&K6Zrsimovi"
MT5_SERVER   = "ICMarketsSC-Demo"

conn = MT5ConnectionParams(
    path=MT5_PATH,
    login=MT5_LOGIN,
    password=MT5_PASSWORD,
    server=MT5_SERVER,
)

trader = MT5Trader(conn=conn)
trader.close_all_positions()
trader.shutdown()
