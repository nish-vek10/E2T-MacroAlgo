# ==== OIL LONG GUI ==== #

import MetaTrader5 as mt5
from baseClass import MT5Trader, MT5ConnectionParams

# --- OPTIONAL: specify a particular terminal + account to use ---
# Leave any of these as None to use the default running MT5 session.
MT5_PATH     = r"C:\MT5\xInterns\terminal64.exe"
MT5_LOGIN    = 52421640
MT5_PASSWORD = "M3Bgywv9$n8mr1"
MT5_SERVER   = "ICMarketsSC-Demo"

def main():
    # Initialize via base class (uses the above credentials/path if provided)
    conn = MT5ConnectionParams(
        path=MT5_PATH,
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER,
    )
    trader = MT5Trader(conn=conn)
    risk_percent = 0.01

    assets = [
        ("XBRUSD", mt5.ORDER_TYPE_BUY, 20),   # BRENT OIL
        ("XTIUSD", mt5.ORDER_TYPE_BUY, 20),    # CRUDE OIL
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="OilLongAuto")

    trader.shutdown()

if __name__ == "__main__":
    main()
