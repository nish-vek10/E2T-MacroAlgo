# ==== RISK OFF GUI ==== #

import MetaTrader5 as mt5
from baseClass import MT5Trader, MT5ConnectionParams

# --- OPTIONAL: specify a particular terminal + account to use ---
# Leave any of these as None to use the default running MT5 session.
MT5_PATH     = r"C:\MT5\52474875\terminal64.exe"
MT5_LOGIN    = 52474875
MT5_PASSWORD = "W7J&K6Zrsimovi"
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
    risk_percent = 0.25

    assets = [
        ("USTEC", mt5.ORDER_TYPE_SELL, 1000),
        ("US500", mt5.ORDER_TYPE_SELL, 500),
        ("DE40", mt5.ORDER_TYPE_SELL, 1000),
        ("USDJPY", mt5.ORDER_TYPE_BUY, 150),
        ("CHFJPY", mt5.ORDER_TYPE_BUY, 150),
        ("XAUUSD", mt5.ORDER_TYPE_BUY, 5000),
        ("EURUSD", mt5.ORDER_TYPE_SELL, 150),
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="RiskOffAuto")

    trader.shutdown()

if __name__ == "__main__":
    main()
