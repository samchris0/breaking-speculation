from celery import Celery

from utils.config import REDDIS_BROKER_URL, REDDIS_RESULT_BACKEND

celery_app = Celery(
    "api_worker",
    broker=REDDIS_BROKER_URL,
    backend=REDDIS_RESULT_BACKEND
)

celery_app.autodiscover_tasks(["fastapi_app.tasks"])
