import json
import logging
import redis
from datetime import datetime
from typing import List, Dict

from news_procesor.celery_app import celery_app
from news_procesor.ingestion_request import ingestion_request
from news_procesor.keywords import KeywordExtractor
from news_procesor.news_fetcher import NewsFetcher
from news_procesor.repository import HeadlineRepository
from news_procesor.utils.merge_tree_deltas import merge_tree_deltas
from news_procesor.utils.result_query import result_query 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.poll_query_updates")
def poll_query_updates(self):
    repo = HeadlineRepository()

    for keyword in repo.retrieve_in_progress_iterator():
        
        # Get corresponding task_id
        task_id = repo.get_task_id_from_keyword(keyword)

        # Check for updates from fast api
        result = result_query(str(task_id)) 
        status = result["status"]

        if status == "failure":
            logger.info(f"Keyword: {keyword} API query failed")
            repo.remove_keyword_from_in_progress(keyword)
            continue

        elif status == "complete":
            logger.info(f"Keyword: {keyword} has no markets")
            repo.remove_keyword_from_in_progress(keyword)
            continue
        
        elif status == "in_progress":
            data = result["data"]
            if data:
                logger.info(f"Keyword: {keyword} data loading")
                repo.keyword_data_set_show_keyword(keyword,True)
        
        elif status == 'success':
            data = result["data"]
            if data:
                logger.info(f"Keyword: {keyword} successfully queried")
                repo.keyword_data_set_show_keyword(keyword,True)

                tree = merge_tree_deltas({},data)
                repo.keyword_data_set_data(keyword,tree)

