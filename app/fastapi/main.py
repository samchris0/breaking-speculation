import functools
import json
import logging

from fastapi import FastAPI

from app.fastapi.api.routes import ingestion

#Initialize app
app = FastAPI()

#Add ingestions route
app.include_router(ingestion.router)


