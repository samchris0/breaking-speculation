from fastapi import APIRouter

from app.fastapi.tasks.ingestion import start_ingestion
from app.fastapi.schemas.ingestion import IngestionRequest

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"]
)

@router.get("/")
async def ingestor(req : IngestionRequest):
    start_ingestion.delay(req.model_dump()) # type: ignore[attr-defined]
    return {"status": "queued"}
