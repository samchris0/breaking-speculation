import asyncio
import httpx
from typing import Any, Dict, List

from core.polymarket_client import PolymarketClient, PolymarketRateLimit, PolymarketUnavailable
from schemas.ingestion import IngestionRequest

# Define semaphore for this module to limit requests
polymarket_sem = asyncio.Semaphore(10)


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
    
    intent = req.intent

    if intent == 'exact':
        return await polymarket_get_event(req, client)
    elif intent == 'keyword':
        return await polymarket_search_keyword(req, client)


async def polymarket_get_event(req: IngestionRequest, client: PolymarketClient) -> List[Dict]:
    """
    return all markets in an event in the format described in polymarker_handler
    """

    #Query metadata of event from Gamma API
    slug = req.query
    resp = await polymarket_query_event_slug(slug, client.gamma)

    # Parse metadata from response
    data = polymarket_get_market_ids(resp)

    # Get price history from CLOB API
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob) for datum in data))

    return data


async def polymarket_search_keyword(req: IngestionRequest, client: PolymarketClient) -> List[Dict]:
    """
    returns all markets related to keyword search in the form described by polymarket_handler
    """

    #Get slugs relating to keyword search
    slugs = await polymarket_get_events_from_keyword(req, client.gamma)

    resps = await asyncio.gather(*(polymarket_query_event_slug(slug, client.gamma) for slug in slugs))

    data = []
    for resp in resps:
        data.append(polymarket_get_market_ids(resp))
    
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob) for datum in data))
    
    return data


async def polymarket_get(client: httpx.AsyncClient, endpoint: str, *,params: dict | None = None,) -> Dict:
    """
    async get request function with error handling
    """
    async with polymarket_sem:
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


async def polymarket_query_event_slug(slug: str, client: httpx.AsyncClient) -> Dict:
    """
    Return polymarket event from slug
    """

    ENDPOINT = f'/events/slug/{slug}'

    resp = await polymarket_get(client=client, endpoint=ENDPOINT)
    
    return resp


async def polymarket_get_events_from_keyword(req: IngestionRequest, client: httpx.AsyncClient) -> List[str]:
    """
    Return polymarket slugs that match keyword search
    """

    ENDPOINT = '/public_search'
    PARAMS = {
        'q' : req.query
    }

    resp = await polymarket_get(client=client, endpoint=ENDPOINT, params=PARAMS)

    events = resp['events']

    event_slugs = []
    for event in events:
        event_slugs.append(event['slug'])
    
    return event_slugs


async def polymarket_price_history(data: Dict, client: httpx.AsyncClient) -> Dict:
    """
    Return price history for a given market and outcome
    """

    ENDPOINT = '/prices-history'
    PARAMS = {
            'market':data['tokenId'],
            'interval':'max'
            }

    resp = await polymarket_get(client=client, endpoint=ENDPOINT, params=PARAMS)

    data['history'] = resp['history']

    return data


def polymarket_get_market_ids(resp: Dict[str, Any]) -> List[Dict]:
    """
    Takes events slug query response and extracts relevant data to query price history
    """

    data = []
    markets = resp['markets']
    for market in markets:
        question = market['question']
        outcomes = market['outcomes']
        tokenIds = market['clobTokenIds']
        for i in range(len(outcomes)):
            data.append({
                'question':question,
                'outcome':outcomes[i],
                'tokenId':tokenIds[i]})

    return data