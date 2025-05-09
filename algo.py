# algo.py
import datetime
import queue
import sys
import time
from enum import IntEnum

from loguru import logger

# from rich.console import Console
# from rich.theme import Theme
from ib_client import IBClient, qu_ask, qu_bid, qu_ctx, qu_orderstatus
from trade import Trade

# pnl_theme = Theme({"gain": "green", "loss": "red"})
# console = Console(theme=pnl_theme)


class OrderType(IntEnum):
    BUY = 1
    SELL = 2


def enter_trade(t: Trade, client: IBClient):
    # check for existing marketdata stream
    # if client.order_id in client.active_streams:
    #     client.cancel_market_data(client.order_id)
    #     logger.info("[Algo] Active Stream, cannot create another stream...")
    #     return None
    # Send request

    t.display()
    client.nextId()
    req = f" reqid: {client.order_id} >>>"
    t.console.print(req + " new reqid created")
    ctx = t.define_contract()
    # Wait for status
    t.console.print(req + " getting contract id from tws")
    client.reqContractDetails(client.order_id, contract=ctx)
    time.sleep(1)
    try:
        msg = qu_ctx.get(timeout=5)
        # console.print(ctx + f"contract id {msg['conId']}")
        t.conid = msg["conId"]
    except queue.Empty:
        logger.info(req + f"Unable to get Contract ID for {t.symbol}...")
        logger.info(req + f"Algo is shutting down for {t.symbol}...")
        client.disconnect()
        sys.exit(1)

    client.nextId()
    t.display()
    t.console.print(req + " getting request id")
    ordfn = t.create_order_fn(reqId=client.order_id, action="BUY")
    client.reqMktData(client.order_id, ctx, "", False, False, [])

    t.console.print("  -------------")
    # Wait for status
    while True:
        try:
            msg = qu_ask.get(timeout=5)
            time_diff = datetime.datetime.now() - msg["time"]
            if time_diff.total_seconds() > 4:
                continue
            t.display()
            buy = t.console.input(f" {req} Buy at {msg['price']} (y/n) ?")
            if buy == "y":
                ord = ordfn(msg["price"])
                client.placeOrder(client.order_id, ctx, ord)
                t.console.print(f" {req} order sent ")
                break
            else:
                continue
        except queue.Empty:
            logger.info(f"[Algo] Waiting for market data for {t.symbol}...")
            continue


def check_order(t: Trade, client: IBClient):
    # allow 5 attempts before cancelling order
    x = 0
    req = f" reqid: {client.order_id} >>>"
    while True:
        try:
            if x == 6:
                pass
                # send cancel order
            msg = qu_orderstatus.get(timeout=5)
            t.console.print(f" {req} Status: {msg['status']} ")
            if msg["status"] == "Filled":
                t.console.print(f" {req} Status: {msg['status']} ")
                t.console.print(f" {req} Entry Price: {msg['avgFillPrice']} ")
                t.entry_price = msg["avgFillPrice"]
                break
            else:
                x = x + 1
                continue
        except queue.Empty:
            t.console.print(f" {req} Status: Waiting fo fill order ")
            continue
            x = x + 1


def exit_trade(t: Trade, client: IBClient):
    # Send request
    client.nextId()
    req = f" reqid: {client.order_id} >>>"
    ctx = t.define_contract()
    ordfn = t.create_order_fn(reqId=client.order_id, action="SELL")

    # Wait for status
    while True:
        try:
            # pnl_pct = getPnlSingle(t, client, account)
            # logger.info(f"[Algo] Latest PnL is {pnl_pct}")
            # get ask price from queue
            # ensure the the price in queue is recent

            msg = qu_bid.get(timeout=5)
            time_diff = datetime.datetime.now() - msg["time"]
            if time_diff.total_seconds() > 4:
                continue
            # TODO - check correct tick type (looking for bid price)
            x = msg["price"] - t.entry_price
            t.console.print("price change: " + str(x))
            t.unreal_pnlval = t.position * (msg["price"] - t.entry_price)
            t.unreal_pnlpct = (msg["price"] - t.entry_price) / t.entry_price

            t.display()
            sell = t.console.input(
                f" {req} + Sell {t.symbol} at {msg['price']} (y/n)? "
            )
            if sell == "y":
                ord = ordfn(msg["price"])
                client.placeOrder(client.order_id, ctx, ord)
                check_order(t, client)
                break
            else:
                continue
        except queue.Empty:
            logger.info(f"[Algo] Waiting for bid price on {t.symbol}...")
            continue
