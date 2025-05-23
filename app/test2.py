import asyncio

from ib_ansync import IB, Stock


async def fetch_data(ib):
    try:
        contract = Stock("AAPL", "SMART", "USD")
        await ib.reqMktData(contract)

        # Process market data
        # ...
    except Exception as e:
        print(f"Error fetching data: {e}")
    finally:
        ib.disconnect()


async def main():
    ib = IB()
    try:
        await ib.connectAsync()
        await fetch_data(ib)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if ib.isConnected():
            await ib.disconnectAsync()


if __name__ == "__main__":
    asyncio.run(main())
