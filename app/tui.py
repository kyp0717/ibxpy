import time
from queue import Queue

from rich.console import Console
from rich.text import Text
from trade import STAGE, Trade

console = Console()


class TUI:
    def __init__(self, console: Console, trade: Trade):
        self.cs = console
        self.tr = trade

    def show_heading(self):
        h = f"\n ********* {self.tr.symbol} ********* "
        wh = Text(h)
        wh.stylize("yellow")
        self.cs.print(wh)

    def show_pnl(self):
        t = f" Unrealized PnL: {self.tr.unreal_pnlval:.2f}"
        wt = Text(t)
        if self.tr.unreal_pnlval == 0:
            wt.stylize("blue")
        elif self.tr.unreal_pnlval < 0:
            wt.stylize("red")
        elif self.tr.unreal_pnlval > 0:
            wt.stylize("green")
        self.cs.print(wt)

    def buy(self, qu: Queue):
        q = f" >>> buy {self.tr.symbol} at {qu['price']}? (y/n) "
        self.cs.print(q, end="")

    def sell(self, qu: Queue):
        q = f" >>> sell {self.tr.symbol} at {qu['price']}? (y/n) "
        self.cs.print(q, end="")

    def show_entry(self):
        h = f" [ ReqID {self.tr.ids.buy} ] Entry Price: {self.tr.entry_price} "
        self.cs.print(h)

    def show_exit(self):
        h = f" [ ReqID {self.tr.ids.sell} ] Exit Price: {self.tr.exit_price} "
        self.cs.print(h)

    def show(self):
        self.cs.clear()
        match self.tr.stage:
            case STAGE.ENTRY:
                h = " [ Trade Status ] Entry "
                self.show_heading()
                self.cs.print(h)
                self.show_pnl()
            case STAGE.ENTERING:
                h = " [ Trade Status ] Buy Order Submitted "
                self.show_heading()
                self.cs.print(h)
                self.show_entry()
                self.show_pnl()
            case STAGE.HOLD:
                h = " [ Trade Status ] Hold "
                self.show_heading()
                self.cs.print(h)
                self.show_entry()
                self.show_pnl()
            case STAGE.EXITING:
                h = " [ Trade Status ] Selling"
                self.show_heading()
                self.cs.print(h)
                self.show_entry()
                self.show_pnl()
            case STAGE.EXIT:
                h = " [ Trade Status ] SOLD"
                self.show_heading()
                self.cs.print(h)
                self.show_entry()
                self.show_exit()
                self.show_pnl()
            case STAGE.DISCONNECT:
                h = " [ Trade Status ] Disconnect"
                self.show_heading()
                self.cs.print(h)
                self.show_entry()
                self.show_exit()
                self.show_pnl()

    def check_entry(self, id, qu: Queue) -> STAGE:
        self.cs.print(f" reqid {id} >>> Status: {qu['status']} ")
        if qu["status"] == "Filled":
            self.cs.print(f" reqid {id} >>> Entry Price: {qu['avgFillPrice']} ")
            self.tr.entry_price = qu["avgFillPrice"]
            return STAGE.HOLD
        else:
            self.cs.print(f" reqid {id} >>> order not filled ")
            time.sleep(1)
            # self.cs.print(qu)
            return STAGE.ENTERING

    def check_exit(self, id, qu: Queue) -> STAGE:
        if self.tr.ids.sell == qu["orderId"]:
            self.cs.print(f" reqid {id} >>> Status: {qu['status']} ")
            if qu["status"] == "Filled":
                self.cs.print(f" reqid {id} >>> Exit Price: {qu['avgFillPrice']} ")
                self.tr.exit_price = qu["avgFillPrice"]
                return STAGE.EXIT
            else:
                self.cs.print(f" reqid {id} >>> order not filled ")
                return STAGE.EXITING
        else:
            return STAGE.EXITING
