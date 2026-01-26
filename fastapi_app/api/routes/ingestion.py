import json
import zlib

from fastapi import APIRouter
from celery.result import AsyncResult

from fastapi_app.core.celery_app import celery_app
from fastapi_app.repositories.async_repository import AsyncIngestionRepository
from fastapi_app.tasks.ingestion import start_ingestion
from fastapi_app.schemas.ingestion import IngestionRequest

redis_repository = AsyncIngestionRepository()

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

    celery_status = result.state
    load_status = await redis_repository.get_status(task_id)
    
    # Check load status
    if load_status is not "PENDING":

        if load_status == "IN_PROGRESS":
            data = await redis_repository.load_tree_deltas(task_id)

            if data:
                # TEST
                print(data[-1]["events"].keys())
                return {"status":"in_progress","data":data}
            else:
                return {"status":"in_progress","data":[]}
        elif load_status == "COMPLETE":
            data = await redis_repository.load_tree_deltas(task_id)

            if data:
                return {"status": "success", "data":data}
            else:
                return {"status": "failure", "error": "Query completed but no data returned"}
        elif load_status == "FAILED":
            query_error = await redis_repository.get_error(task_id)
            return {"status": "failure", "error": query_error}
        else:
            return {"status":"failure", "error": f"Unknown loading status: {load_status}"}    
    
    # If there is no load status check celery task health
    if celery_status == "PENDING":
        return {"status": "pending"}
    elif celery_status == "FAILURE":
        return {"status": "failure", "error": str(result.result)}
    else:
        return {"status": celery_status.lower()}
