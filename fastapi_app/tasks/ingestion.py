"""
This module creates a celery task to begin the query. One query per task.
"""

import asyncio
import json
import zlib

from pydantic import TypeAdapter

from fastapi_app.core.celery_app import celery_app
from fastapi_app.core.sync_redis import sync_redis
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.services.dispatcher import dispatcher

@celery_app.task(bind=True)
def start_ingestion(self, req_dict):
    
    # Repopulate model at process boundary for type security, 
    adapter = TypeAdapter(IngestionRequest)
    req = adapter.validate_python(req_dict)
    
    # Start event loop and run query
    asyncio.run(dispatcher(api_request = req, task_id = self.request.id))

    

