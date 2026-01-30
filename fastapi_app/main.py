import logging

from fastapi import FastAPI

from fastapi_app.api.routes import ingestion

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

setup_logging()

#Initialize app
app = FastAPI()

#Add ingestions route
app.include_router(ingestion.router)

