from rich.console import Console
from rich.text import Text

from trade import Trade


class TUI:
    def __init__(self, trade: Trade, console: Console):
        console = console
        trade = trade

    def run(self):
        pass

        k

    def heading(self):
        heading = f"[yellow] \n********* {self.symbol} ********* [/yellow] "
        unrealval = Text(f"${self.trade.unreal_pnlval:.2f}")
        unrealpct = Text(f"{self.trade.unreal_pnlpct * 100:.2f}%")
        if self.unreal_pnlval == 0:
            unrealval.stylize("blue")
            unrealpct.stylize("blue")
            pnl = f" PnL (%): {unrealval} ({unrealpct}) "
        elif self.unreal_pnlval > 0:
            heading = f"[green] \n********* {self.symbol} ********* [/green] "
            pnl = f"[green] PnL (%): {unrealval} ({unrealpct}) [/green]"
            unrealval.stylize("green")
            unrealpct.stylize("green")
        else:
            heading = f"[red] \n********* {self.symbol} ********* [/red] "
            pnl = f"[red] PnL (%): {unrealval} ({unrealpct}) [/red]"
            unrealval.stylize("red")
            unrealpct.stylize("red")

        self.console.print(heading)
        self.console.print(pnl)
        self.console.print(" -----------------------")

    def pnl(self):
        pass

    def entry_panel(self):
        pass
