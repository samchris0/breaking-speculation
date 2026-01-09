"""
This module creates a 
"""

import asyncio

from pydantic import TypeAdapter

from core.celery_app import celery_app
from schemas.ingestion import IngestionRequest
from services.dispatcher import dispatcher


@celery_app.task(bind=True)
def start_ingestion(self, req_dict):
    adapter = TypeAdapter(IngestionRequest)
    req = adapter.validate_python(req_dict)
    asyncio.run(dispatcher(req))

