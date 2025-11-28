#####   C-L-O-S-E  A-L-L   #####

from baseClass import MT5Trader, MT5ConnectionParams

# --- OPTIONAL: specify a particular terminal + account to use ---
MT5_PATH     = r"C:\MT5\xInterns\terminal64.exe"
MT5_LOGIN    = 52421640
MT5_PASSWORD = "M3Bgywv9$n8mr1"
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
