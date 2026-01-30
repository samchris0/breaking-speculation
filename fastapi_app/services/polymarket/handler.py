import asyncio
import logging

from fastapi_app.core.polymarket_client import PolymarketClient
from fastapi_app.core.celery_logging_config import get_logger
from fastapi_app.repositories.async_repository import AsyncIngestionRepository
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.schemas.intent import ExactSearch, KeywordSearch
from fastapi_app.services.polymarket.client import polymarket_get_events_from_keyword, polymarket_price_history, polymarket_query_event_slug
from fastapi_app.services.polymarket.parsing import polymarket_get_market_ids, create_tree, add_market_to_tree, market_to_tree_delta

logger = get_logger(__name__)

async def polymarket_handler(req: IngestionRequest, client: PolymarketClient, task_id: str):
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
    
    redis_repository = AsyncIngestionRepository()

    # Define semaphore for this module to limit requests, semaphore must be created in each event loop or asyncio.run will cause error
    polymarket_sem = asyncio.Semaphore(10) 

    search = req.search

    if isinstance(search, ExactSearch):
        await polymarket_search_event(slug = req.search_term, client = client, semaphore = polymarket_sem, repo = redis_repository, task_id = task_id)
    elif isinstance(search, KeywordSearch):
        await polymarket_search_keyword(keyword = req.search_term, limit = req.search.limit, client = client, semaphore = polymarket_sem, repo = redis_repository, task_id = task_id) #type:ignore 
    else:
        raise TypeError("search must be exact or keyword")
    
async def polymarket_search_event(slug: str, client: PolymarketClient, semaphore: asyncio.Semaphore, repo: AsyncIngestionRepository, task_id: str):
    """
    return all markets in an event in the format described in polymarker_handler
    """

    # Query metadata of event from Gamma API
    event = await polymarket_query_event_slug(slug, client.gamma, semaphore)

    # Parse metadata from response
    data = polymarket_get_market_ids(event)

    tasks = [polymarket_price_history(datum, client.clob, semaphore) for datum in data]

    tree = create_tree()
    
    await repo.data_loading_status_start(task_id)

    try:
        for coroutine in asyncio.as_completed(tasks):
            result = await coroutine

            # Append raw market data to list of raw market data for logging
            await repo.save_raw_market(task_id, result)

            # Update tree 
            tree = add_market_to_tree(tree, result)
            await repo.save_tree(task_id, tree)
        
        # Set loading status to complete
        await repo.data_loading_status_end(task_id)

    except Exception as e:
        await repo.data_loading_status_failed(task_id)
        await repo.set_error(task_id,e)
        raise

async def polymarket_search_keyword(keyword : str, limit : int, client: PolymarketClient, semaphore: asyncio.Semaphore, repo: AsyncIngestionRepository, task_id: str):
    """
    returns all markets related to keyword search in the form described by polymarket_handler
    """
    
    print("ENTERED polymarket_search_keyword")

    # Get list of events relating to keyword search
    events = await polymarket_get_events_from_keyword(keyword, limit, client.gamma, semaphore)

    data = []
    for event in events:
        data.extend(polymarket_get_market_ids(event))
    
    tasks = [polymarket_price_history(datum, client.clob, semaphore) for datum in data]

    # Set loading status to in progress
    await repo.data_loading_status_start(task_id)

    try:
        for index, coroutine in enumerate(asyncio.as_completed(tasks)):
            
            result = await coroutine
            
            # Append raw market data to list of raw market data for logging
            await repo.save_raw_market(task_id, result)
            
            # Update tree (No longer needed?)
            #tree = add_market_to_tree(tree, result)

            # Create tree update dict
            tree_delta = market_to_tree_delta(result)

            logger.debug(tree_delta)

            await repo.save_tree_delta(task_id, tree_delta)

        # Set loading status to complete
        await repo.data_loading_status_end(task_id)

    except Exception as e:
        await repo.data_loading_status_failed(task_id)
        await repo.set_error(task_id,e)
        raise
