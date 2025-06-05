import argparse
import cmd
import queue
import sys
import threading
import time

import key_listener as kl
from ib_client import IBClient, qu_ask, qu_bid, qu_contract, qu_orderstatus
from rich.console import Console
from trade import STAGE, Trade
from tui import TUI

# Create an ArgumentParser object
parser = argparse.ArgumentParser(description="get symbol and quantity")

# Add arguments
parser.add_argument("symbol", type=str, help="symbol")
parser.add_argument("size", type=int, help="size")
# Parse the arguments
args = parser.parse_args()

cs = Console()
cs.clear()

## Must instantiate the client first because it carries the console instance
client = IBClient()
client.connect("127.0.0.1", 7500, clientId=1001)
## delay market data
## set to 1 for real-time market data
client.reqMarketDataType(1)
# ibclient_thread = threading.Thread(target=start_ib_client, args=(client,), daemon=True)
ibclient_thread = threading.Thread(target=client.run, daemon=True)
ibclient_thread.start()
# Wait for next valid order ID to give time for thread to start up
while client.order_id is None:
    time.sleep(0.5)

t = Trade(symbol=args.symbol, position=args.size)
t.ids.initial = client.order_id
t.define_contract()

cmd = cmd.Cmd(client=client, trade=t)

cmd.get_contract()
t.ids.contract = client.order_id
# get method is blocking
c = qu_contract.get(timeout=2)
t.conid = c["conId"]
t.define_contract()
# request market data
cmd.stream_mkt_data()
t.ids.market_data = client.order_id

tui = TUI(console=cs, trade=t)

while True:
    # TODO: capture error message
    # TODO: capture order history
    tui.show()
    match t.stage:
        case STAGE.ENTRY:
            try:
                msg = qu_ask.get(timeout=1)
                tui.buy(msg)
                input = kl.get_single_key()
                cs.print(input)
                if input == "y":
                    cmd.buy_limit(msg["price"])
                    t.ids.buy = client.order_id
                    cs.print(
                        f"\n [ reqid {client.order_id} ] buy limit order submitted ",
                        end="",
                    )
                    t.stage = STAGE.ENTERING
            except queue.Empty:
                # TODO: provide the option to cancel the order and exit app
                cs.print(f" [ reqid {client.order_id} ] ask queue empty")
                cs.print(f" [ reqid {client.order_id} ] waiting for ask price")
                time.sleep(1)
        case STAGE.ENTERING:
            try:
                ordstat = qu_orderstatus.get(timeout=1)
                t.stage = tui.check_entry(client.order_id, ordstat)
            except queue.Empty:
                cs.print(f" [ reqid {client.order_id} ] order status queue empty")
                time.sleep(0.5)
        case STAGE.HOLD:
            try:
                msg = qu_bid.get(timeout=2)
                t.unreal_pnlval = t.position * (msg["price"] - t.entry_price)
                t.unreal_pnlpct = (msg["price"] - t.entry_price) / t.entry_price
                tui.sell(msg)
                input = kl.get_single_key()
                cs.print(input)
                if input == "y":
                    cmd.sell_limit(msg["price"])
                    cs.print(
                        f"\n [ reqid {client.order_id} ] sell limit order submitted ",
                        end="",
                    )
                    t.stage = STAGE.EXITING
                else:
                    continue
                    # time.sleep(1)
            except queue.Empty:
                cs.print(f" [ reqid {client.order_id} ] bid queue empty")
                cs.print(f" [ reqid {client.order_id} ] waiting for bid price")
                time.sleep(1)
        case STAGE.EXITING:
            try:
                ordstat = qu_orderstatus.get(timeout=1)
                t.stage = tui.check_exit(client.order_id, ordstat)
            except queue.Empty:
                cs.print(f" [ reqid {client.order_id} ] order status queue empty")
                time.sleep(1)
        case STAGE.EXIT:
            # tui.show()
            s = cs.input(" >>> Disconnect from client? (y/n)")
            if s == "y":
                client.disconnect()
                t.stage = STAGE.DISCONNECT
                cs.print(" [ Algo ] Disconnecting from TWS...")
        case STAGE.DISCONNECT:
            # tui.show()
            s = cs.input(" >>> Shutdown Algo? (y/n)")
            if s == "y":
                cs.print(" [ Algo ] Shutting down!")
                break

ibclient_thread.join()
sys.exit(0)
