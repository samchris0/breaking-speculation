from celery import Celery

from app.utils.config import REDDIS_BROKER_URL, REDDIS_RESULT_BACKEND

celery_app = Celery(
    "worker",
    broker=REDDIS_BROKER_URL,
    backend=REDDIS_RESULT_BACKEND
)