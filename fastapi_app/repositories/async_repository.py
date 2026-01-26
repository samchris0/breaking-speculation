from redis.asyncio import Redis

from fastapi_app.core.async_redis import build_async_client
from fastapi_app.repositories.ingestion_repository import IngestionRepository 

class AsyncIngestionRepository(IngestionRepository):
    def __init__(self):
        self.redis: Redis = build_async_client()

    async def save_raw_market(self, task_id: str, market: dict):
        raw_key = self._raw_key(task_id)
        serialized_market = self._serialize(market)
        await self.redis.rpush(raw_key, serialized_market) #type: ignore

    async def get_raw_markets(self, task_id: str):
        raw_key = self._raw_key(task_id)
        raw_markets = await self.redis.lrange(raw_key, 0, -1) #type: ignore
        markets = self._deserialize_many(raw_markets)
        return markets

    async def save_tree(self, task_id: str, tree: dict):
        tree_key = self._tree_key(task_id)
        dicted_tree = self._tree_to_dict(tree)
        serialized_tree = self._serialize(dicted_tree)
        await self.redis.set(
            tree_key,
            serialized_tree
        )

    async def load_tree(self, task_id: str) -> dict: 
        tree_key = self._tree_key(task_id)
        raw_data = await self.redis.get(tree_key)
        data = self._deserialize(raw_data)
        return data

    async def save_tree_delta(self, task_id: str, tree_delta: dict):
        tree_delta_key = self._tree_delta_key(task_id)
        serialized_delta = self._serialize(tree_delta)
        await self.redis.rpush(tree_delta_key, serialized_delta) #type: ignore
    
    async def load_tree_deltas(self, task_id: str):
        tree_delta_key = self._tree_delta_key(task_id)
        raw_deltas = await self.redis.lrange(tree_delta_key, 0, -1) #type: ignore
        deltas = self._deserialize_many(raw_deltas)
        return deltas

    async def get_status(self, task_id: str) -> str:
        load_key = self._load_key(task_id)
        status = await self.redis.get(load_key)
        if status is None:
            return "PENDING"
        return status.decode("utf-8")
    
    async def data_loading_status_start(self, task_id: str):
        load_key = self._load_key(task_id)
        start_status = "IN_PROGRESS"
        await self.redis.set(load_key, start_status)
    
    async def data_loading_status_end(self, task_id: str):
        load_key = self._load_key(task_id)
        end_status = "COMPLETE"
        await self.redis.set(load_key, end_status)

    async def data_loading_status_failed(self, task_id: str):
        load_key = self._load_key(task_id)
        failed_status = "FAILED"
        await self.redis.set(load_key, failed_status)

    async def set_error(self, task_id: str, error: Exception):
        error_key = self._error_key(task_id)
        error_str = str(error)
        await self.redis.set(error_key, error_str)

    async def get_error(self, task_id: str):
        error_key = self._error_key(task_id)
        error = await self.redis.get(error_key)
        if error is None:
            return "Unknown error"
        return error.decode("utf-8")   