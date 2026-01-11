from app.fastapi.core.polymarket_client import PolymarketClient
from app.fastapi.schemas.ingestion import IngestionRequest, PolymarketIngestion, KalshiIngestion
from app.fastapi.services.polymarket import polymarket_handler

async def dispatcher(req : IngestionRequest):
    match req:
        case PolymarketIngestion():
            client = PolymarketClient()

            try:
                await polymarket_handler(req, client)
            finally:
                await client.close()
        case KalshiIngestion():
            pass
        

