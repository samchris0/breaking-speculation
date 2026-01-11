from fastapi import APIRouter

from app.fastapi.tasks.ingestion import start_ingestion
from app.fastapi.schemas.ingestion import IngestionRequest

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"]
)

@router.post("/")
async def ingestor(req : IngestionRequest):
    task = start_ingestion.delay(req.model_dump()) # type: ignore[attr-defined]
    return {"status": "queued", "task_id": task.id}
