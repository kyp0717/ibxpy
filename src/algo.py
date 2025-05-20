# algo.py
import datetime
import queue
import sys
import time

from loguru import logger

from ib_client import IBClient, qu_ask, qu_bid, qu_ctx, qu_orderstatus
from trade import Trade


def enter(t: Trade, client: IBClient):
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
    t.console.print(req + " getting contract id ")
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
    ordfn = t.create_order_fn(reqId=client.order_id, action="BUY", ordertype="LMT")
    client.reqMktData(client.order_id, ctx, "", False, False, [])

    t.console.print("  -------------")
    # Wait for status
    while True:
        try:
            msg = qu_ask.get(timeout=5)
            time_diff = datetime.datetime.now() - msg["time"]
            if time_diff.total_seconds() > 2:
                continue
            t.display()
            buy = t.console.input(f"{req} Buy at {msg['price']} (y/n) ?")
            if buy == "y":
                ord = ordfn(msg["price"])
                client.placeOrder(client.order_id, ctx, ord)
                t.console.print(f"{req} buy order sent ")
                break
            else:
                continue
        except queue.Empty:
            t.console.print(f"{req} Waiting for ask price for {t.symbol}...")
            continue
        time.sleep(1)


def check_buy_order(t: Trade, client: IBClient):
    # allow 5 attempts before cancelling order
    x = 0
    req = f" reqid: {client.order_id} >>>"
    while True:
        try:
            # msg_ask = qu_ask.get(timeout=5)
            if x == 4:
                pass
                # after 4 tries - cancel order
                # client.cancelOrder(client.order_id)
                # t.console.print(f"{req} Order Cancel ")
                # send cancel order
            msg_ordstatus = qu_orderstatus.get(timeout=5)
            t.console.print(f"{req} TWS Status: {msg_ordstatus['status']} ")
            # t.console.print(f"{req} TWS ReqMktData: {msg_ask['price']} ")
            if msg_ordstatus["status"] == "Filled":
                t.console.print(f"{req} Status: {msg_ordstatus['status']} ")
                t.console.print(f"{req} Entry Price: {msg_ordstatus['avgFillPrice']} ")
                t.entry_price = msg_ordstatus["avgFillPrice"]
                t.console.print(f"{req} Moving to tracking stage ")
                break
            else:
                x = x + 1
                # time.sleep(1)
                continue
        except queue.Empty:
            t.console.print(f"{req} buy order status - empty queue  ")
            continue
            x = x + 1


def check_sell_order(t: Trade, client: IBClient, bid_price: float):
    # allow 5 attempts before cancelling order
    x = 0
    req = f" [ SELL ] reqid: {client.order_id} >>>"
    while True:
        try:
            t.display()
            t.console.print(f"{req} trying #{x} ")
            msg_bid = qu_bid.get(timeout=5)
            t.console.print(f"{req} Current bid {msg_bid['price']} ")
            if x == 6:
                t.console.print(f"{req} Liquidating ... ")
                liquidate(t, client, msg_bid["price"])
                break

                # send cancel order
            ordstatus = qu_orderstatus.get(timeout=5)
            t.console.print(f"{req} Order Status: {ordstatus['status']} ")
            if (
                ordstatus["orderId"] == client.order_id
                and ordstatus["status"] == "Filled"
            ):
                t.console.print(f"{req} whole msg: {ordstatus} ")
                t.console.print(f"{req} Exit Price: {ordstatus['avgFillPrice']} ")
                t.exit_price = ordstatus["avgFillPrice"]
                t.display()
                break
            else:
                # if order is not filled, wait 1 second
                x = x + 1
                continue
        except queue.Empty:
            t.console.print(f"{req} bid price queue is empty ")
            x = x + 1
            continue


def liquidate(t: Trade, client: IBClient, price: float):
    # Send request
    req = f" [ SELL MKT ] reqid: {client.order_id} >>>"
    ctx = t.define_contract()
    ordfn = t.create_order_fn(reqId=client.order_id, action="SELL", ordertype="MKT")
    ord = ordfn(price)
    client.placeOrder(client.order_id, ctx, ord)
    t.console.print(f" {req} Liquidate {t.symbol} at {price} ")


def exit(t: Trade, client: IBClient, price: float):
    # Send request
    client.nextId()
    req = f" [ SELL ] reqid: {client.order_id} >>>"
    ctx = t.define_contract()
    ordfn = t.create_order_fn(reqId=client.order_id, action="SELL", ordertype="LMT")
    ord = ordfn(price)
    client.placeOrder(client.order_id, ctx, ord)
    t.console.print(f"{req} Order submitted - Sell {t.symbol} at {price} ")
    check_sell_order(t, client, price)


def track(t: Trade, client: IBClient):
    # Wait for status
    while True:
        try:
            # pnl_pct = getPnlSingle(t, client, account)
            # logger.info(f"[Algo] Latest PnL is {pnl_pct}")
            # get ask price from queue
            # ensure the the price in queue is recent

            msg = qu_bid.get(timeout=5)
            # time_diff = datetime.datetime.now() - msg["time"]
            # if time_diff.total_seconds() > 4:
            #     continue
            # TODO - check correct tick type (looking for bid price)
            x = msg["price"] - t.entry_price
            t.console.print(f" [ HOLD ] >>> price change: {x:.2f}")
            t.unreal_pnlval = t.position * (msg["price"] - t.entry_price)
            t.unreal_pnlpct = (msg["price"] - t.entry_price) / t.entry_price

            t.display()
            sell = t.console.input(
                f" [ HOLD ] >>> Current Bid at {msg['price']} - Sell (y/n)? "
            )
            if sell == "y":
                exit(t, client, msg["price"])
                break
            else:
                # time.sleep(1)
                continue
        except queue.Empty:
            req = f" reqid: {client.order_id} >>>"
            t.console.print(f"{req} no bid price in queue ")
            # time.sleep(1)
            continue
