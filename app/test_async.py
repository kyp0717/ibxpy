import asyncio

from ib_async import IB


async def get_current_time():
    ib = IB()
    await ib.connect(
        "127.0.0.1", 7500, clientId=1
    )  # Use 7496 for live accounts or 7497 for paper
    try:
        current_time = await ib.req_current_time()
        print(f"Current IB server time: {current_time}")
    finally:
        await ib.disconnect()


if __name__ == "__main__":
    asyncio.run(get_current_time())
