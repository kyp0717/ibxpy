# ib_client.py

import datetime
import queue

from ibapi.client import EClient
from ibapi.wrapper import ContractDetails, EWrapper
from loguru import logger

# use to pass msg btw algo module to IB App
algo_request = queue.Queue()

# messages coming from TWS (which is coming from remote server)
tws_response = queue.Queue()
qu_ask = queue.Queue()
qu_ctx = queue.Queue()
qu_bid = queue.Queue()
qu_orderstatus = queue.Queue()
qu_pnl = queue.Queue()
qu_pnlsingle = queue.Queue()


class IBClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.order_id = None
        self.active_streams = set()

    def nextValidId(self, orderId):
        logger.info(f"[IB] Next valid order ID: {orderId}")
        self.order_id = orderId

    def nextId(self):
        self.order_id += 1

    def error(self, reqId, errorCode, errorString, advanceOrderReject):
        logger.error(f" --- ReqId: {reqId} --- ")
        logger.error(f"ErrorCode: {errorCode}, ErrorString: {errorString}")
        logger.error(f"ErrorString: {errorString}")
        logger.error(f"Order Reject: {advanceOrderReject} ")

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        msg = {"reqId": reqId, "conId": contractDetails.contract.conId}
        qu_ctx.put(msg)

    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ):
        msg = {
            "orderId": orderId,
            "status": status,
            "filled": filled,
            "remaining": remaining,
            "avgFillPrice": avgFillPrice,
        }
        qu_orderstatus.put(msg)
        logger.info(msg)

    def execDetails(self, reqId, contract, execution):
        msg = {
            "type": "execution",
            "symbol": contract.symbol,
            "execId": execution.execId,
            "shares": execution.shares,
            "price": execution.price,
        }
        tws_response.put(msg)

    def tickPrice(self, reqId, tickType, price, attrib):
        timestamp = datetime.datetime.now()
        msg = {
            "reqId": reqId,
            "tickType": tickType,
            "price": price,
            "attrib": attrib,
            "time": timestamp,
        }
        if tickType == 2:
            qu_ask.put(msg)
        if tickType == 1:
            qu_bid.put(msg)
        # logger.info(msg)

    def cancelMarketData(self, ticker_id):
        if ticker_id in self.active_streams:
            self.cancelMktData(ticker_id)
            self.active_streams.remove(ticker_id)
            logger.info(f"Stopped market data stream for {ticker_id}")
        else:
            logger.info(f"No active stream to cancel for {ticker_id}")

    def clear_queue(q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        timestamp = datetime.datetime.now()
        msg = {
            "reqId": reqId,
            "unrealizedPnL": unrealizedPnL,
            "time": timestamp,
        }
        qu_pnl.put(msg)

    def pnlSingle(
        self,
        reqId: int,
        pos: float,
        dailyPnL: float,
        unrealizedPnL: float,
        realizedPnL: float,
        value: float,
    ):
        msg = {"reqId": reqId, "unrealizedPnL": unrealizedPnL, "value": value}
        qu_pnlsingle.put(msg)


def start_ib_client(app):
    app.run()
