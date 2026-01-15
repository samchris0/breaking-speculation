import asyncio
import httpx
import json
from typing import Any, Dict, List

from fastapi_app.core.polymarket_client import PolymarketClient, PolymarketRateLimit, PolymarketUnavailable
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.schemas.intent import ExactSearch, KeywordSearch

async def polymarket_handler(req: IngestionRequest, client: PolymarketClient):
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

    # Define semaphore for this module to limit requests
    polymarket_sem = asyncio.Semaphore(10) 

    search = req.search

    if isinstance(search, ExactSearch):
        return await polymarket_search_event(slug = req.search_term, client = client, semaphore = polymarket_sem)
    elif isinstance(search, KeywordSearch):
        return await polymarket_search_keyword(keyword = req.search_term, limit = req.search.limit, client = client, semaphore = polymarket_sem) #type:ignore 


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
        # 
        data.extend(polymarket_get_market_ids(event))
    
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob, semaphore) for datum in data))
    
    return data


async def polymarket_get(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, endpoint: str, *,params: dict | None = None,) -> Dict:
    """
    async get request function with error handling
    """
    async with semaphore:
        try:
            resp = await client.get(endpoint, params=params)
        except httpx.TimeoutException as e:
            raise PolymarketUnavailable() from e

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code == 429:
        raise PolymarketRateLimit()

    if resp.status_code >= 500:
        raise PolymarketUnavailable()

    resp.raise_for_status()

    raise PolymarketUnavailable()


async def polymarket_query_event_slug(slug: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> Dict:
    """
    Return polymarket event from slug
    """

    ENDPOINT = f'/events/slug/{slug}'

    resp = await polymarket_get(client=client, semaphore=semaphore, endpoint=ENDPOINT)
    
    return resp

async def polymarket_get_events_from_keyword(keyword: str, limit: int, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> List[Dict]:
    """
    Return polymarket slugs that match keyword search
    """

    ENDPOINT = '/public-search'
    PARAMS = {
        'q' : keyword,
        'limit_per_type' : limit
    }

    resp = await polymarket_get(client=client, semaphore=semaphore, endpoint=ENDPOINT, params=PARAMS)

    events = resp.get('events',[])

    return events


async def polymarket_price_history(data: Dict, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> Dict:
    """
    Return price history for a given market and outcome
    """

    ENDPOINT = '/prices-history'
    PARAMS = {
            'market':data['tokenId'],
            'interval':'max'
            }

    resp = await polymarket_get(client=client, semaphore=semaphore, endpoint=ENDPOINT, params=PARAMS)

    data['history'] = resp.get('history',[])

    return data


def polymarket_get_market_ids(event: Dict[str, Any]) -> List[Dict]:
    """
    Takes events slug query response and extracts relevant data to query price history
    """

    data = []
    markets = event['markets']
    for market in markets:
        question = market['question']
        
        # Polymarket API wraps these lists with a string "["...", "..."]"
        outcomes = json.loads(market['outcomes'])
        tokenIds = json.loads(market['clobTokenIds'])
        
        for i in range(len(outcomes)):
            data.append({
                'question':question,
                'outcome':outcomes[i],
                'tokenId':tokenIds[i]})

    print(data)

    return data