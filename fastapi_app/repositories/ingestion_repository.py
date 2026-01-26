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
        return f"ingestion:{task_id}:error"
    
    def _tree_delta_key(self, task_id: str) -> str:
        return f"ingestion:{task_id}:tree_delta"

    # Use msgpack.packb()?
    def _serialize(self, data: dict | list) -> bytes:
        return zlib.compress(json.dumps(data).encode())

    # Use msgpack.unpackb()?
    def _deserialize(self, payload: bytes) -> dict:
        return json.loads(zlib.decompress(payload))
    
    def _deserialize_many(self, payloads) -> list[dict]:
        return [self._deserialize(p) for p in payloads]

    def _tree_to_dict(self, tree: dict) -> dict:
        # Recursively turn defaultdicts into dicts for serialization
        if isinstance(tree, dict):
            return {k: self._tree_to_dict(v) for k, v in tree.items()}
