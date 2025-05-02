# algo.py
import datetime
import queue
import sys
import time

from ib_client import IBClient, qu_ask, qu_bid, qu_ctx, qu_orderstatus, qu_pnlsingle
from loguru import logger

from trade import Trade

# import logging
logger.remove()  # Remove the default
logger.add(sys.stderr, level="TRACE")


def enter_trade(t: Trade, client: IBClient):
    # check for existing marketdata stream
    # if client.order_id in client.active_streams:
    #     client.cancel_market_data(client.order_id)
    #     logger.info("[Algo] Active Stream, cannot create another stream...")
    #     return None
    # Send request
    client.nextId()
    ctx = t.define_contract()
    # Wait for status
    client.reqContractDetails(client.order_id, contract=ctx)
    time.sleep(1)
    try:
        msg = qu_ctx.get(timeout=5)
        logger.info(f"[Algo] ReqId {msg['reqId']} - Getting Contract Detail")
        t.conid = msg["conId"]
        logger.info(
            f"[Algo] ReqId {msg['reqId']}: ConId for {t.symbol} - {msg['conId']}"
        )
    except queue.Empty:
        logger.info(f"[Algo] Unable to get Contract ID for {t.symbol}...")
        logger.info(f"[Algo] Algo is shutting down for {t.symbol}...")
        client.disconnect()
        sys.exit(1)

    client.nextId()
    ordfn = t.create_order_fn(reqId=client.order_id, action="BUY")
    client.reqMktData(client.order_id, ctx, "", False, False, [])

    # Wait for status
    while True:
        try:
            msg = qu_ask.get(timeout=5)
            time_diff = datetime.datetime.now() - msg["time"]
            if time_diff.total_seconds() > 4:
                continue
            logger.info(f"[Algo] ReqId {msg['reqId']} - Ask {msg['price']}")
            buy = input(f"Buy {t.symbol} at {msg['price']} (y/n)")
            if buy == "y":
                ord = ordfn(msg["price"])
                client.placeOrder(client.order_id, ctx, ord)
                break
            else:
                continue
        except queue.Empty:
            logger.info(f"[Algo] Waiting for market data for {t.symbol}...")
            continue


def check_order(t: Trade, client: IBClient):
    while True:
        try:
            msg = qu_orderstatus.get(timeout=5)
            logger.info(f"OrderId {msg['orderId']} - Order Status ")
            logger.info(f"Order Status - {msg['status']} ")
            if msg["status"] == "Filled":
                logger.info(f"AverageFillPrice - {msg['avgFillPrice']} ")
                t.avgFillPrice = msg["avgFillPrice"]
                break
            else:
                continue
        except queue.Empty:
            logger.info(f"[Algo] Waiting to fill order for {t.symbol}...")
            continue


def getPnlSingle(t: Trade, client: IBClient, account: str) -> float:
    client.nextId()

    pnl_pct = 0.0
    # Wait for status
    while True:
        client.reqPnLSingle(
            reqId=client.order_id, account=account, modelCode="", conid=t.conid
        )
        # wait for TWS to run callback
        time.sleep(1)
        try:
            msg = qu_pnlsingle.get(timeout=5)
            # pnl = msg["unrealizedPnL"]
            value = msg["value"]
            logger.info(f"[Algo] UnrealizedPnL: ${msg['unrealizedPnL']} ")
            logger.info(f"[Algo] Position Value: ${msg['value']} ")
            pnl_pct = (value - (t.avgFillPrice * t.position)) / value * 100
            logger.info(f"Unrealize PNL pct: {pnl_pct}")
            break

        except queue.Empty:
            logger.info(f"[Algo] Waiting PNL for {t.symbol}...")
            continue

    return pnl_pct


def exit_trade(t: Trade, client: IBClient):
    # Send request
    client.nextId()
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
            logger.info(f"ReqId {msg['reqId']} bid: {msg['price']} ")
            pnl_val = t.position * (t.avgFillPrice - msg["price"])
            logger.info(f"ReqId {msg['reqId']} pnl:  {pnl_val}")
            sell = input(f"Sell {t.symbol} at {msg['price']} (y/n)")
            if sell == "y":
                logger.info(f"ReqId {msg['reqId']} ... attempting to sell {t.symbol}")
                ord = ordfn(msg["price"])
                client.placeOrder(client.order_id, ctx, ord)
                check_order(t, client)
                break
            else:
                continue
        except queue.Empty:
            logger.info(f"[Algo] Waiting for bid price on {t.symbol}...")
            continue
