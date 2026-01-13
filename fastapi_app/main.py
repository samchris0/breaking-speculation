import functools
import json
import logging

from fastapi import FastAPI

from fastapi_app.api.routes import ingestion

#Initialize app
app = FastAPI()

#Add ingestions route
app.include_router(ingestion.router)


