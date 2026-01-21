import asyncio
import httpx
from typing import Any, Dict, List

from fastapi_app.core.polymarket_client import PolymarketClient, PolymarketRateLimit, PolymarketUnavailable
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.schemas.intent import ExactSearch, KeywordSearch

async def polymarket_query_event_slug(slug: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> Dict:
    """
    Return polymarket event from slug
    """

    ENDPOINT = f'/events/slug/{slug}'

    resp = await polymarket_get(client=client, semaphore=semaphore, endpoint=ENDPOINT)
    
    return resp

async def polymarket_get_events_from_keyword(keyword: str, limit: int, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> List[Dict]:
    """
    Return polymarket list of polymarket events that 
    """

    ENDPOINT = '/public-search'
    PARAMS = {
        'q' : keyword,
        'limit_per_type' : limit
    }

    resp = await polymarket_get(client=client, semaphore=semaphore, endpoint=ENDPOINT, params=PARAMS)

    events = resp.get('events',[])

    return events

# Fix this to take into count new nested structure of markets but keep async
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

    if data['history']:
        # API returns results in long format [{t: ..., p: ...}, {t: ..., p: ...}]. Convert to wide to speed serialization
        data['history'] = {key: [d[key] for d in data['history']] for key in data['history'][0]}

    return data

async def polymarket_get(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, endpoint: str, *,params: dict | None = None,) -> Dict:
    """
    async get polymarket get function with error handling
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