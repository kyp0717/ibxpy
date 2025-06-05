# main.py

from ib_async import IB, Stock

# from ib_worker import start_ib_worker
from loguru import logger

logger.remove()  # Remove the default
# logger.add(sys.stderr, level="TRACE", format="{time} | {level} | {message}")
logger.add("test.log", mode="w", level="TRACE")
# logger.add(sys.stderr, level="TRACE")

ib = IB()
ib.connect("127.0.0.1", 7500, clientId=1001)

ib.reqMarketDataType(1)  # Use free, delayed, frozen data
contract = Stock("AAPL")


asset = tui.prompt("define asset")
trade(asset)
