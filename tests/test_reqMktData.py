# main.py

import threading
import time

from ib_client import IBClient, start_ib_client
from ib_worker import start_ib_worker

from algo import run_algo

# Instantiate app
# this must be done first to create queue to be imported
client = IBClient()
client.connect("127.0.0.1", 7500, clientId=1001)

# Start IB API client in background
threading.Thread(target=start_ib_client, args=(client,), daemon=True).start()

# Wait for next valid order ID
while client.order_id is None:
    time.sleep(0.1)

# Start IB worker loop in a thread
start_ib_worker(client)

# Start the trading algorithm in a thread
run_algo()

# Optionally keep main thread alive
while True:
    time.sleep(1)
