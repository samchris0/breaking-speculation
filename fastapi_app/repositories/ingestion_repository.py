import json 
import zlib

from fastapi_app.core.async_redis import build_async_client
from fastapi_app.core.sync_redis import build_sync_client

class IngestionRepository():

    def _tree_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:tree"

    def _raw_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:raw"
    
    def _load_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:load"
    
    def _error_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:load"
    
    # Use msgpack.packb()?
    def _serialize(self, data: dict | list) -> bytes:
        return zlib.compress(json.dumps(data).encode())

    # Use msgpack.unpackb
    def _deserialize(self, payload: bytes) -> dict:
        return json.loads(zlib.decompress(payload))
    
    def _tree_to_dict(self, tree: dict) -> dict:
        # Recursively turn defaultdicts into dicts for serialization
        if isinstance(tree, dict):
            return {k: self._tree_to_dict(v) for k, v in tree.items()}


class AsyncIngestionRepository(IngestionRepository):
    def __init__(self):
        self.redis = build_async_client()

    async def save_raw_market(self, task_id: str, market: dict):
        raw_key = self._raw_key(task_id)
        serialized_market = self._serialize(market)
        await self.redis.rpush(raw_key, serialized_market)

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
    
    async def get_status(self, task_id: str) -> str:
        load_key = self._load_key(task_id)
        return await self.redis.get(load_key)
    
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
        return await self.redis.get(error_key)    

class SyncIngestionRepository(IngestionRepository):
    def __init__(self):
        self.redis = build_sync_client()

    def save_raw_market(self, task_id: str, market: dict):
        raw_key = self._raw_key(task_id)
        serialized_market = self._serialize(market)
        self.redis.rpush(raw_key, serialized_market)

    def save_tree(self, task_id: str, tree: dict):
        tree_key = self._tree_key(task_id)
        dicted_tree = self._tree_to_dict(tree)
        serialized_tree = self._serialize(dicted_tree)
        self.redis.set(
            tree_key,
            serialized_tree
        )

    def load_tree(self, task_id: str) -> dict: 
        tree_key = self._tree_key(task_id)
        raw_data = self.redis.get(tree_key)
        data = self._deserialize(raw_data)
        return data
    
    def get_status(self, task_id: str) -> str:
        load_key = self._load_key(task_id)
        return self.redis.get(load_key)
    
    def data_loading_status_start(self, task_id: str):
        load_key = self._load_key(task_id)
        start_status = "IN_PROGRESS"
        self.redis.set(load_key, start_status)

    def data_loading_status_end(self, task_id: str):
        load_key = self._load_key(task_id)
        end_status = "COMPLETE"
        self.redis.set(load_key, end_status)
    
    def data_loading_status_failed(self, task_id:str):
        load_key = self._load_key(task_id)
        failed_status = "FAILED"
        self.redis.set(load_key, failed_status)