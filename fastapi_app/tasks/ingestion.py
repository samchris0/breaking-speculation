"""
This module creates a celery task to begin the query. One query per task.
"""

import asyncio

from pydantic import TypeAdapter

from fastapi_app.core.celery_app import celery_app
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.services.dispatcher import dispatcher

@celery_app.task(bind=True)
def start_ingestion(self, req_dict):
    
    # Repopulate model at process boundary for type security, 
    adapter = TypeAdapter(IngestionRequest)
    req = adapter.validate_python(req_dict)
    
    # Start event loop and run query
    results = asyncio.run(dispatcher(req))
    return results


