from dataclasses import dataclass
from enum import Enum

from ibapi.client import Contract, Order
from rich.console import Console


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
        self.stoploss: float = 0.0
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

    def display(self):
        # self.console.clear()

        heading = "  [yellow underline]Trade [/yellow underline] | [yellow underline]Unreal PnL (%) [/yellow underline]"
        if self.unreal_pnlval > 0:
            pnl = f"  {self.symbol}   | [green]${self.unreal_pnlval:.2f} ({self.unreal_pnlpct:.2f}%)[/green] "
        elif self.unreal_pnlval < 0:
            pnl = f"  {self.symbol}   | [red]${self.unreal_pnlval:.2f} ({self.unreal_pnlpct:.2f}%)[/red] "
        else:
            pnl = f"  {self.symbol}   | [blue]${self.unreal_pnlval:.2f} ({self.unreal_pnlpct:.2f}%)[/blue] "

        self.console.print(heading)
        self.console.print(pnl)
        self.console.print("  -----------------------")
