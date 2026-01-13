from fastapi_app.core.polymarket_client import PolymarketClient
from fastapi_app.schemas.ingestion import IngestionRequest, PolymarketIngestion, KalshiIngestion
from fastapi_app.services.polymarket import polymarket_handler

async def dispatcher(req : IngestionRequest):
    match req:
        case PolymarketIngestion():
            client = PolymarketClient()
            try:
                result = await polymarket_handler(req, client)
            finally:
                await client.close()
            return result

        case KalshiIngestion():
            pass
        

