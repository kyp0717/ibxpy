# ib_client.py

import datetime
import queue

from ibapi.client import EClient
from ibapi.wrapper import ContractDetails, EWrapper
from loguru import logger

# messages coming from TWS (which is coming from remote server)
qu_ask = queue.Queue()
qu_error = queue.Queue()
qu_contract = queue.Queue()
qu_bid = queue.Queue()
qu_orderstatus = queue.Queue()
order_history = {}
qu_pnl = queue.Queue()
qu_pnlsingle = queue.Queue()


class IBClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.order_id = None
        self.contract_id = None
        self.order_history_index = 0

    def nextValidId(self, orderId):
        logger.info(f"[IB] Next valid order ID: {orderId}")
        self.order_id = orderId

    def nextId(self):
        self.order_id += 1

    def error(self, reqId, errorCode, errorString, advanceOrderReject):
        msg = {
            "reqId": reqId,
            "errorCode": errorCode,
            "errorString": errorString,
            "orderReject": advanceOrderReject,
        }
        qu_error.put(msg)

    def contractDetails(self, reqId, contractDetails: ContractDetails):
        msg = {"reqId": reqId, "conId": contractDetails.contract.conId}
        qu_contract.put(msg)

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
        self.order_history_index += 1
        msg = {
            "entry": self.order_history_index,
            "orderId": orderId,
            "status": status,
            "filled": filled,
            "remaining": remaining,
            "avgFillPrice": avgFillPrice,
        }
        # order_history[self.order_history_index] = msg
        qu_orderstatus.put(msg)

    def execDetails(self, reqId, contract, execution):
        msg = {
            "type": "execution",
            "symbol": contract.symbol,
            "execId": execution.execId,
            "shares": execution.shares,
            "price": execution.price,
        }
        _ = msg
        # tws_response.put(msg)

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

    def sell_remaining(self, orderId):
        self.reqOpenOrders()
        order = self.Order()
        order.action = "SELL"
        order.orderType = "LMT"
        order.totalQuantity = 100
        order.lmtPrice = 200  # Higher than market to delay fill

        self.order_filled_qty[orderId] = 0
        self.order_remaining_qty[orderId] = order.totalQuantity
        self.order_status[orderId] = "Submitted"

        self.placeOrder(orderId, self.contract, order)


def start_ib_client(app):
    app.run()
