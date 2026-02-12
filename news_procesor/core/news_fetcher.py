import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from google_news_feed import GoogleNewsFeed

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news from Google News RSS."""
    
    def __init__(self,max_headlines=12):
        self.gnf = GoogleNewsFeed(
            language='en',
            country='US'
        )
        self.max_headlines = max_headlines
    
    def fetch_headlines(self, topic: Optional[str] = None) -> list:

        try:
            if topic is None:
                
                logger.info(f"Fetching headlines")

                news_items = self.gnf.top_headlines()
                headlines = self.parse_newsitems(news_items)
                return headlines

            else:

                logger.info(f"Fetching news for topic: {topic}")

                news_items = self.gnf.query_topic(topic)
                headlines = self.parse_newsitems(news_items)
                return headlines
                
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
        
    def parse_newsitems(self, news_items):
        
        headlines = []
        for item in news_items[:self.max_headlines]:
            try:
                headline = {
                    "title": getattr(item,"title",None),
                    "url": getattr(item,"link",None),
                    "published": getattr(item,"pubdate",None),
                    "source": getattr(item, "source", None),
                    "description": getattr(item, "description", None),
                    "fetched_at": datetime.now(timezone.utc)
                }
                
                # Only add if title
                if headline["title"]:
                    headlines.append(headline)
                
            except Exception as e:
                logger.warning(f"Error processing news item: {e}")
                continue
    
        logger.info(f"Successfully fetched {len(headlines)} headlines")
        
        return headlines