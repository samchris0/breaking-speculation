import asyncio
from collections import defaultdict
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

    # Define semaphore for this module to limit requests, semaphore must be created in each event loop or asyncio.run will cause error
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
        data.extend(polymarket_get_market_ids(event))
    
    data = await asyncio.gather(*(polymarket_price_history(datum, client.clob, semaphore) for datum in data))
    

    data = format_event_data(data=data)

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


def polymarket_get_market_ids(event: Dict[str, Any]) -> List[Dict]:
    """
    Takes events slug query response and extracts relevant data to query price history
    """

    data = []
    event_title = event['title']
    event_id = event['id']
    markets = event['markets']
    event_image = event['image']
    for market in markets:
        
        market_question = market['question']
        
        # Polymarket API wraps these lists with a string "["...", "..."]"
        outcomes = json.loads(market['outcomes'])
        clobTokenIds = market.get('clobTokenIds',[])
        volume = market['volumeNum']
        market_id = market['id']
        
        # Check if the the market has a CLOB orderbook, otherwise price history not available
        if clobTokenIds:
            tokenIds = json.loads(market['clobTokenIds'])

            for i in range(len(outcomes)):
                next_market = {
                        'provider':'polymarket',
                        'event_id':event_id,
                        'event_title':event_title,
                        'event_image':event_image,
                        'market_id':market_id,
                        'market_question': market_question, 
                        'outcome':outcomes[i], 
                        'tokenId':tokenIds[i],
                        'volume':volume
                        }
                
                data.append(next_market)

    return data


def materialize_polymarket(flat_rows: List[Dict]) -> Dict: 
    
    # Create 
    tree = defaultdict(
        lambda: {
            #might not be necessary
            "title": None,
            "image":None,
            "markets": defaultdict(
                lambda: {
                    "question": None,
                    "volume":None,
                    "outcomes": []
                }
            )
        }
    )

    for row in flat_rows:
        event_id = row['event_id']
        market_id = row['market_id']

        # Define event node
        event = tree[event_id]

        # Populate event node
        event["title"] = row["event_title"]
        event["image"] = row["event_image"]

        # Define market node
        market = event["markets"][market_id]

        #Populate market node
        market["question"] = row["market_question"]
        market["volume"] = row["volume"]
        market["outcomes"].append(
            {
                'provider':row['provider'],
                'tokenId':row['tokenId'],
                'outcome':row['outcome'],
                'history':row['history']
            }
        )
    
    return tree
