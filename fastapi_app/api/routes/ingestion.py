import json
import zlib

from fastapi import APIRouter
from celery.result import AsyncResult

from fastapi_app.core.celery_app import celery_app
from fastapi_app.core.async_redis import async_redis
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

    #Add redis ingestion tag
    task_id = f"ingestion:{task_id}"

    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "FAILURE":
        return {"status": "failure", "error": str(result.result)}
    elif result.state == 'SUCCESS':
        
        # Get results from task_id
        data_bytes = await async_redis.get(task_id) 

        if data_bytes:
            # Decompress data
            data = json.loads(
                    zlib.decompress(data_bytes).decode("utf-8")
            )
            return {'status': 'success', 'data': data}
        else:
            return {
                "status": "failed",
                "error": "Query finished successfully but no results were found"
            }  
    else:
        return {"status": result.state.lower()}