from typing import List

from fastapi_app.core.polymarket_client import PolymarketClient
from fastapi_app.schemas.ingestion import IngestionRequest, PolymarketIngestion, KalshiIngestion
from fastapi_app.services.polymarket.handler import polymarket_handler

async def dispatcher(api_request : IngestionRequest, task_id : str):
# Checks for service provider and dispatches request to the correct handler for API queries

    match api_request:
        case PolymarketIngestion():
            client = PolymarketClient()
            try:
                await polymarket_handler(api_request, client, task_id)
            finally:
                await client.close()
            

        case KalshiIngestion():
            result = {}
            pass
    
    # Send result to data normalizer
    # formatted_results = normalize_data(result)
    # (Or should I make a different return path? e.g sent results to normalize_data and return from there?)
    # For now return list of results
    # return list(result.values())

