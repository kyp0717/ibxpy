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
            # order.outsideRth = False
            order.outsideRth = True
            return order

        return create_order

    def display(self):
        # self.console.clear()
        # Define a fixed-width format for alignment

        heading = f"[yellow] ********* {self.symbol} ********* [/yellow] "
        unrealval = Text(f"${self.unreal_pnlval:.2f}")
        unrealpct = Text(f"{self.unreal_pnlpct * 100:.2f}%")
        if self.unreal_pnlval == 0:
            unrealval.stylize("blue")
            unrealpct.stylize("blue")
            pnl = f" PnL (%): {unrealval} ({unrealpct}) "
        elif self.unreal_pnlval > 0:
            heading = f"[green] ********* {self.symbol} ********* [/green] "
            pnl = f"[green] PnL (%): {unrealval} ({unrealpct}) [/green]"
            unrealval.stylize("green")
            unrealpct.stylize("green")
        else:
            heading = f"[red] ********* {self.symbol} ********* [/red] "
            pnl = f"[red] PnL (%): {unrealval} ({unrealpct}) [/red]"
            unrealval.stylize("red")
            unrealpct.stylize("red")

        entry_price = f"${self.entry_price:.2f} "
        exit_price = f"${self.exit_price:.2f} "
        stop_loss = f"${self.stop_loss:.2f} "

        self.console.print(heading)
        self.console.print(pnl)
        self.console.print(f" Entry: {entry_price} ")
        self.console.print(f" Exit: {exit_price} ")
        self.console.print(f" Stop Loss: {stop_loss}")
        self.console.print(" -----------------------")

    def display2(self):
        heading1 = f"[yellow] *********** {self.symbol} ********* [/yellow] "
        entry_head = f"[orange underline] {'Entry':<6} [/orange underline] "
        hold_head = f"[orange underline] {'Hold':<6} [/orange underline] "
        exit_head = f"[orange underline] {'Exit':<6} [/orange underline] "
        self.console.print(heading1)
        self.console.print(entry_head + hold_head + exit_head)
