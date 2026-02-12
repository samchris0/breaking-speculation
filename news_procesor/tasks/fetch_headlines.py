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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOPICS = ["WORLD", "NATION", "BUSINESS", "TECHNOLOGY", "ENTERTAINMENT", "SPORTS", "SCIENCE", "HEALTH"]

@celery_app.task(bind=True, name="tasks.fetch_and_process_news")
def fetch_and_process_news(self):
    logger.info("Initializing task")
    repo = HeadlineRepository()
    
    logger.info("Updating display information")
    repo.shift_current_headlines()

    logger.info("")

    for topic in TOPICS:
        repo.shift_current_topic_headlines(topic)

    logger.info("Starting news ingestion")
    
    news_fetcher = NewsFetcher()
    keyword_extractor = KeywordExtractor()

    headlines = news_fetcher.fetch_headlines()
    headlines = keyword_extractor.extract_from_headlines(headlines)
    query_keywords(repo, headlines)

    # Save to redis
    repo.store_new_headlines(headlines)

    for topic in TOPICS:
        headlines = news_fetcher.fetch_headlines(topic)
        headlines = keyword_extractor.extract_from_headlines(headlines)
        query_keywords(repo, headlines)

        # Save to redis
        repo.store_new_topic_headlines(topic, headlines)


def query_keywords(repo: HeadlineRepository, headlines:list):
    
    for headline in headlines:
        
        keywords = headline.get('keywords')
        if keywords:
            for keyword in keywords:
                active_keyword = repo.check_for_keyword(keyword)

                if active_keyword:
                    continue
                else:
                    
                    results = ingestion_request(keyword)
                    keyword_data = {
                                    "task_id":results["task_id"],
                                    "status":"in_progress",
                                    "show_keyword":False,
                                    "data":{}
                                    }
                    repo.add_keyword_data(keyword, keyword_data)

