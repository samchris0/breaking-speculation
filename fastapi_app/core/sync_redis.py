import os
import redis

def build_sync_client():
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/2")

    sync_redis = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=False,
    )

    return sync_redis
