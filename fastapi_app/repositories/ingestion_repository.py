import json 
import zlib

class IngestionRepository:
    def __init__(self, redis_client):
        self.redis = redis_client

    def _tree_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:tree"

    def _raw_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:raw"
    
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


class SyncIngestionRepository(IngestionRepository):

    def load_tree(self, ingestion_id: str):
        payload = self.redis.get(self._tree_key(ingestion_id))
        return None if not payload else self._deserialize(payload)

    def save_tree(self, ingestion_id: str, tree: dict):
        self.redis.set(
            self._tree_key(ingestion_id),
            self._serialize(tree),
        )