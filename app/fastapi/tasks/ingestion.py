"""
This module creates a 
"""

import asyncio

from pydantic import TypeAdapter

from app.fastapi.core.celery_app import celery_app
from app.fastapi.schemas.ingestion import IngestionRequest
from app.fastapi.services.dispatcher import dispatcher

@celery_app.task(bind=True)
def start_ingestion(self, req_dict):
    adapter = TypeAdapter(IngestionRequest)
    req = adapter.validate_python(req_dict)
    results = asyncio.run(dispatcher(req))
    return results


