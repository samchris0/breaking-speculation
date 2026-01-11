import httpx
import atexit
import asyncio

async_client = httpx.AsyncClient()

@atexit.register
def close_client():
    asyncio.run(async_client.aclose())