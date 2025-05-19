# main.py

import sys
import threading
import time

# from ib_worker import start_ib_worker
from loguru import logger

import algo
from ib_client import IBClient, console
from trade import Trade

# import logging
logger.remove()  # Remove the default
# logger.add(sys.stderr, level="TRACE", format="{time} | {level} | {message}")
logger.add("test.log", mode="w", level="TRACE")
# logger.add(sys.stderr, level="TRACE")

## Must instantiate the client first because it carries the console instance
client = IBClient()
client.connect("127.0.0.1", 7500, clientId=1001)

## delay market data
## set to 1 for real-time market data
client.reqMarketDataType(1)
# Start IB API client in background
# pnl_theme = Theme({"profit": "green", "loss": "red"})
# cs = Console(theme=pnl_theme)
# define the asset to trade
t = Trade(symbol="KO", position=10, console=console)
paper_account = "DU1591287"
real_account = "U2008021"
# Instantiate app
# this must be done first to create queue to be imported
msg = f" [ {t.symbol} ] IB client instantiated"
logger.info(msg)
console.clear()
console.print(msg)


msg = f" [ {t.symbol} ] Starting ib client thread"
logger.info(msg)
console.print(msg)
# ibclient_thread = threading.Thread(target=start_ib_client, args=(client,), daemon=True)
ibclient_thread = threading.Thread(target=client.run, daemon=True)
ibclient_thread.start()

# Wait for next valid order ID
while client.order_id is None:
    time.sleep(0.1)


# Start the trading algorithm in main thread
msg = f" [ {t.symbol} ] Starting algo ..."
logger.info(msg)
console.print(msg)

orderfn = algo.enter(t, client)
algo.check_buy_order(t, client, orderfn)
algo.track(t, client)


s = console.input("Shutdown Algo? (y/n)")

if s == "y":
    client.disconnect()
    console.print("\nDisconnecting from TWS...")
    ibclient_thread.join()
    sys.exit(0)
