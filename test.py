from texts import send_sms
import asyncio

async def test():
    await send_sms('6034984589', 'test')

asyncio.run(test())