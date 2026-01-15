from fastapi import APIRouter
from celery.result import AsyncResult

from fastapi_app.core.celery_app import celery_app
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
    else:
        return {"status": "done", "data": result.result}
