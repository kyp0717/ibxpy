from dataclasses import dataclass
from enum import Enum

from ibapi.client import Contract, Order
from rich.console import Console
from rich.text import Text


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
    def __init__(self, symbol, position: int, console: Console):
        self.symbol: str = symbol
        self.size: int = 0
        self.position = position
        self.stop_loss: float = 0.0
        self.entry_price: float = 0.0
        self.exit_price: float = 0.0
        self.conid = None
        self.unreal_pnlval: float = 0.0
        self.unreal_pnlpct: float = 0.0
        self.console = console

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
    def create_order_fn(self, reqId: int, action: str, ordertype: str):
        order = Order()

        def create_order(lmtprice: float):
            order.symbol = self.symbol
            order.orderId = reqId
            order.action = action
            order.orderType = ordertype
            order.lmtPrice = lmtprice
            order.totalQuantity = self.position
            order.outsideRth = True
            return order

        return create_order

    def display(self, unrealval: float, unrealpct: float):
        # self.console.clear()
        # Define a fixed-width format for alignment

        heading = (
            f"[yellow underline] ******* {self.symbol} ******* [/yellow underline] |"
        )

        unrealval = Text(f"${self.unreal_pnlval:.2f}")
        unrealpct = Text(f"{self.unreal_pnlpct:.3f}")
        if unrealval == 0:
            unrealval.stylize("blue")
            unrealpct.stylize("blue")
        elif unrealval > 0:
            unrealval.stylize("green")
            unrealpct.stylize("green")
        else:
            unrealval.stylize("red")
            unrealpct.stylize("green")

        entry_price = f"${self.entry_price:.2f} |"
        exit_price = f"${self.entry_price:.2f} "
        stop_loss = f"${self.stop_loss:.2f} "

        self.console.print(heading)
        self.console.print(f" PnL (%): {unrealval} ({unrealpct})")
        self.console.print(f" Entry//Exit: {entry_price} --- ({exit_price})")
        self.console.print(f" Stop Loss: {stop_loss}")
        self.console.print("  -----------------------")
