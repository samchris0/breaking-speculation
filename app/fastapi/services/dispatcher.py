from core.polymarket_client import PolymarketClient
from schemas.ingestion import IngestionRequest

from polymarket import polymarket_handler

async def dispatcher(req : IngestionRequest):
    provider = req.provider

    if provider == 'polymarket':
        client = PolymarketClient()

        try: 
            await polymarket_handler(req, client)
        finally:
            await client.close()

    if provider == 'kalshi':
        pass


