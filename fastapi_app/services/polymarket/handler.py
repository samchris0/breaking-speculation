import asyncio
from typing import Any, Dict, List

from fastapi_app.core.polymarket_client import PolymarketClient
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.schemas.intent import ExactSearch, KeywordSearch
from fastapi_app.services.polymarket.client import polymarket_get_events_from_keyword, polymarket_price_history, polymarket_query_event_slug
from fastapi_app.services.polymarket.parsing import materialize_polymarket, polymarket_get_market_ids

async def polymarket_handler(req: IngestionRequest, client: PolymarketClient) -> Dict:
    """
    Intake ingestion request, parse intent, query data, and return a list of dicts with the following format:

    data : Dict
        {
        question : question that describes the market
        outcome : outcome being considered e.g. yes or no
        tokenId : unique identifier for market and outcome
        history : list of dicts in the form 
                    {t: time,p: price}
        }

    """

    # Define semaphore for this module to limit requests, semaphore must be created in each event loop or asyncio.run will cause error
    polymarket_sem = asyncio.Semaphore(10) 

    search = req.search

    if isinstance(search, ExactSearch):
        data = await polymarket_search_event(slug = req.search_term, client = client, semaphore = polymarket_sem)
    elif isinstance(search, KeywordSearch):
        data =  await polymarket_search_keyword(keyword = req.search_term, limit = req.search.limit, client = client, semaphore = polymarket_sem) #type:ignore 
    else:
        raise TypeError("search must be exact or keyword")
    
    # Format flat data into hierchical polymarket structure, dict
    format_data = materialize_polymarket(data)
    return format_data
    
async def polymarket_search_event(slug: str, client: PolymarketClient, semaphore: asyncio.Semaphore) -> List[Dict]:
    """
    return all markets in an event in the format described in polymarker_handler
    """

    # Query metadata of event from Gamma API
    event = await polymarket_query_event_slug(slug, client.gamma, semaphore)

    # Parse metadata from response
    data = polymarket_get_market_ids(event)

    # Get price history from CLOB API
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob, semaphore) for datum in data))

    return data


async def polymarket_search_keyword(keyword : str, limit : int, client: PolymarketClient, semaphore: asyncio.Semaphore) -> List[Dict]:
    """
    returns all markets related to keyword search in the form described by polymarket_handler
    """

    # Get list of events relating to keyword search
    events = await polymarket_get_events_from_keyword(keyword, limit, client.gamma, semaphore)

    data = []
    for event in events:
        data.extend(polymarket_get_market_ids(event))
    
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob, semaphore) for datum in data))

    return data