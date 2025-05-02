# main.py

import sys
import threading
import time

from ib_client import IBClient

# from ib_worker import start_ib_worker
from loguru import logger

import algo
from trade import Trade

# import logging
logger.remove()  # Remove the default
# logger.add(sys.stderr, level="TRACE", format="{time} | {level} | {message}")
logger.add(sys.stderr, level="TRACE")

# define the asset to trade
t = Trade(symbol="AAPL", position=10)
paper_account = "DU1591287"
# Instantiate app
# this must be done first to create queue to be imported
logger.info("IB client instantiated")
client = IBClient()
client.connect("127.0.0.1", 7500, clientId=1001)

## delay market data
client.reqMarketDataType(3)
# Start IB API client in background

logger.info("Starting ib client thread")
# ibclient_thread = threading.Thread(target=start_ib_client, args=(client,), daemon=True)
ibclient_thread = threading.Thread(target=client.run, daemon=True)
ibclient_thread.start()

# Wait for next valid order ID
while client.order_id is None:
    time.sleep(0.1)


# Start the trading algorithm in main thread
logger.info("Starting algo ...")
algo.enter_trade(t, client)
algo.check_order(t, client)
algo.exit_trade(t, client)


s = input("Shutdown Algo? (y/n)")
if s == "y":
    client.disconnect()
    print("\nDisconnecting from TWS...")
    ibclient_thread.join()
    sys.exit(0)
