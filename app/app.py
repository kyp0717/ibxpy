import cmd

from rich.console import Console

import trade as t

cs = Console()
cs.clear()

asset = cs.input("Define asset: ")
t = t.Trade(asset)

while True:
    match t.stage:
        case ENTRY:
            price = cmd.get_ask()
            cs.print(f"buy {t.symbol} at {price}? ")
            algo.enter(price)
        case HOLD:
            price = cmd.get_bid()
        case EXIT:
            price = cmd.get_bid()
            algo.exit(price)
