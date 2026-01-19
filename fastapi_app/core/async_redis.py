import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/2")

async_redis = Redis.from_url(
    REDIS_URL,
    decode_responses=False,
)
