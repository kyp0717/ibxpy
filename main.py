# main.py

import sys
import threading
import time

# from ib_worker import start_ib_worker
from loguru import logger
from rich.console import Console

import algo
from ib_client import IBClient
from trade import Trade

# import logging
logger.remove()  # Remove the default
# logger.add(sys.stderr, level="TRACE", format="{time} | {level} | {message}")
logger.add("./test.log", mode="w", level="TRACE")
# logger.add(sys.stderr, level="TRACE")

cs = Console()
# define the asset to trade
t = Trade(symbol="AAPL", position=10, console=cs)
paper_account = "DU1591287"
# Instantiate app
# this must be done first to create queue to be imported
msg = f" [ {t.symbol} ] IB client instantiated"
logger.info(msg)
cs.clear()
cs.print(msg)

client = IBClient()
client.connect("127.0.0.1", 7500, clientId=1001)

## delay market data
client.reqMarketDataType(3)
# Start IB API client in background

msg = f" [ {t.symbol} ] Starting ib client thread"
logger.info(msg)
cs.print(msg)
# ibclient_thread = threading.Thread(target=start_ib_client, args=(client,), daemon=True)
ibclient_thread = threading.Thread(target=client.run, daemon=True)
ibclient_thread.start()

# Wait for next valid order ID
while client.order_id is None:
    time.sleep(0.1)


# Start the trading algorithm in main thread
msg = f" [ {t.symbol} ] Starting algo ..."
logger.info(msg)
cs.print(msg)

algo.enter_trade(t, client)
algo.check_order(t, client)
algo.exit_trade(t, client)


s = cs.input("Shutdown Algo? (y/n)")
if s == "y":
    client.disconnect()
    cs.print("\nDisconnecting from TWS...")
    ibclient_thread.join()
    sys.exit(0)
