import functools
import json
import logging

import aioredis
from fastapi import FastAPI
from api.routes import ingestion


#Initialize app
app = FastAPI()

#Add ingestions route
app.include_router(ingestion.router)

#Change this to initialize from db folder?
redis = aioredis.from_url("redis://localhost")

