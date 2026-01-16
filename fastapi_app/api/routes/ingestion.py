import json
import zlib

from fastapi import APIRouter
from celery.result import AsyncResult

from fastapi_app.core.celery_app import celery_app
from fastapi_app.core.redis import redis_client
from fastapi_app.tasks.ingestion import start_ingestion
from fastapi_app.schemas.ingestion import IngestionRequest

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"]
)

# General ingestion request
@router.post("/")
async def ingestor(req : IngestionRequest):
    # Serialize req model and send to ingestion task, mode=json to handle nested classes
    task = start_ingestion.delay(req.model_dump(mode="json")) # type: ignore[attr-defined]
    return {"status": "queued", "task_id": task.id}

# Check ingestion task
@router.get("/{task_id}")
async def check_request(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
       
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "FAILURE":
        return {"status": "failed", "error": str(result.result)}
    elif result.state == 'SUCCESS':
        
        # Get results from task_id
        data_bytes = await redis_client.get(task_id) 

        if data_bytes:
            # Decompress data
            data = json.loads(
                    zlib.decompress(data_bytes).decode("utf-8")
            )
            return {'status': 'success', 'data': data}
        else:
            return{'Error: Query finished sucessfully with no results'}   
    else:
        return {"status": result.state.lower()}