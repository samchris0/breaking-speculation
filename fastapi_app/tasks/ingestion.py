"""
This module creates a celery task to begin the query. One query per task.
"""

import asyncio
import json
import zlib

from pydantic import TypeAdapter

from fastapi_app.core.celery_app import celery_app
from fastapi_app.core.redis import redis_client
from fastapi_app.schemas.ingestion import IngestionRequest
from fastapi_app.services.dispatcher import dispatcher

@celery_app.task(bind=True)
def start_ingestion(self, req_dict):
    
    # Repopulate model at process boundary for type security, 
    adapter = TypeAdapter(IngestionRequest)
    req = adapter.validate_python(req_dict)
    
    # Start event loop and run query
    results = asyncio.run(dispatcher(req))

    # Add parsing logic here to standardize returns from different APIs

    # Convert to serialize then convert to bytes for improved storage/access
    payload = zlib.compress(
        json.dumps(results).encode("utf-8")
    )

    redis_client.setex(
        f"ingestion:{self.request.id}",
        300, #Store for 5 minutes  
        payload
    )


