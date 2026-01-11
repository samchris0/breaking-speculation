from fastapi import APIRouter
from celery.result import AsyncResult

from app.fastapi.core.celery_app import celery_app
from app.fastapi.tasks.ingestion import start_ingestion
from app.fastapi.schemas.ingestion import IngestionRequest

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"]
)

# General ingestion request
@router.post("/")
async def ingestor(req : IngestionRequest):
    task = start_ingestion.delay(req.model_dump()) # type: ignore[attr-defined]
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
