from ib_client import IBClient
from trade import STAGE, Trade


class Cmd:
    def __init__(self, client: IBClient, trade: Trade):
        self.client = client
        self.trade = trade

    def buy_limit(self, price):
        self.client.nextId()
        self.trade.ids.buy = self.client.order_id
        # self.trade.entry_price = price
        ordfn = self.trade.create_order_fn(
            reqId=self.client.order_id, action="BUY", ordertype="LMT"
        )
        ord = ordfn(price)
        self.client.placeOrder(self.client.order_id, self.trade.contract, ord)

    def sell_limit(self, price):
        self.client.nextId()
        self.trade.ids.sell = self.client.order_id
        # self.trade.exit_price = price
        ordfn = self.trade.create_order_fn(
            reqId=self.client.order_id, action="SELL", ordertype="LMT"
        )
        ord = ordfn(price)
        self.client.placeOrder(self.client.order_id, self.trade.contract, ord)

    def get_contract(self):
        self.client.nextId()
        self.trade.ids.contract = self.client.order_id
        self.client.reqContractDetails(
            self.client.order_id, contract=self.trade.contract
        )

    def stream_mkt_data(self):
        self.client.nextId()
        self.trade.ids.market_data = self.client.order_id
        self.client.reqMktData(
            self.client.order_id, self.trade.contract, "", False, False, []
        )
        self.trade.stage = STAGE.ENTRY
