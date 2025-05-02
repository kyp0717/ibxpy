from dataclasses import dataclass
from enum import Enum

from ibapi.client import Contract, Order


class TradeSignal(Enum):
    BUY = 1
    SELL = 2
    HOLD = 3


@dataclass
class PriceChange:
    val: float = 0.0
    cct: float = 0.0


@dataclass
class TrackId:
    buy: int = None
    sell: int = None
    reqMktData: int = None


class Trade:
    def __init__(self, symbol, position: int):
        self.symbol: str = symbol
        self.size: int = 0
        self.position = position
        self.stoploss: float = 0.0
        self.avgFillPrice: float = 0.0
        self.conid = None

    def price_change(self, last) -> PriceChange:
        v1 = self.trade_entry - self.last
        v2 = v1 / last * 100
        self.priceChange.val = v1
        self.priceChange.pct = v2

    def price_change_pct(self, price) -> float:
        v1 = self.trade_entry - self.last
        v2 = v1 / price * 100
        return v2

    def define_contract(self) -> Contract:
        contract = Contract()
        contract.symbol = self.symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        contract.primaryExchange = "NASDAQ"
        return contract

    # order is define in the tickPrice function
    # price dependency
    def create_order_fn(self, reqId: int, action: str):
        order = Order()

        def create_order(lmtprice: float):
            order.symbol = self.symbol
            order.orderId = reqId
            order.action = action
            order.orderType = "LMT"
            order.lmtPrice = lmtprice
            order.totalQuantity = self.position
            order.outsideRth = True
            return order

        return create_order
