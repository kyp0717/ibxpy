from dataclasses import dataclass
from enum import Enum

import ibapi as ibc


class STAGE(Enum):
    CONNECT = 1
    ENTRY = 2
    ENTERING = 3
    HOLD = 4
    EXIT = 5
    EXITING = 6
    DISCONNECT = 7


@dataclass
class PriceChange:
    val: float = 0.0
    cct: float = 0.0


@dataclass
class TWSReqId:
    initial: int = None
    contract: int = None
    buy: int = None
    sell: int = None
    market_data: int = None
    cancel: int = None
    liquidate: int = None


class Trade:
    def __init__(self, symbol, position: int):
        self.ids: TWSReqId = TWSReqId()
        self.symbol: str = symbol
        self.contract = None
        self.stage: STAGE = None
        self.size: int = 0
        self.position = position
        self.stop_loss: float = 0.0
        self.entry_price: float = 0.0
        self.exit_price: float = 0.0
        self.conid = None

        self.unreal_pnlval: float = 0.0
        self.unreal_pnlpct: float = 0.0

        # TODO: Add order history to so that we can confirm order status

    def define_contract(self):
        contract = ibc.client.Contract()
        contract.symbol = self.symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        contract.primaryExchange = "NASDAQ"
        self.contract = contract

    def create_order_fn(self, reqId: int, action: str, ordertype: str):
        order = ibc.client.Order()

        def create_order(lmtprice: float):
            order.symbol = self.symbol
            order.orderId = reqId
            order.action = action
            order.orderType = ordertype
            order.lmtPrice = lmtprice
            order.totalQuantity = self.position
            # order.outsideRth = False
            order.outsideRth = True
            return order

        return create_order
