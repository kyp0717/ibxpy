def getPnlSingle(t: Trade, client: IBClient, account: str) -> (float, float):
    req = f" reqid: {client.order_id} >>>"
    client.nextId()
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
            pnl = msg["value"]
            pnl_pct = (pnl - (t.avgFillPrice * t.position)) / pnl * 100
            t.display()
            t.console.print(req)
            break

        except queue.Empty:
            t.console.print(f" {req} Status: Waiting pnl data ")
            continue

    return pnl_pct
