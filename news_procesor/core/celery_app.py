from celery import Celery
from utils.config import REDDIS_BROKER_URL, REDDIS_RESULT_BACKEND, NEWS_FETCH_INTERVAL_MINUTES

celery_app = Celery(
    "news-processor",
    broker=REDDIS_BROKER_URL,
    backend=REDDIS_RESULT_BACKEND,
    include=["news-processor.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=420,  # 7 minutes max per task
    task_soft_time_limit=360,  # 6 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

celery_app.conf.beat_schedule = {
    "fetch-and-process-news": {
        "task": "tasks.fetch_and_process_news",
        "schedule": NEWS_FETCH_INTERVAL_MINUTES * 60.0,  # Convert to seconds
        "options": {
            "expires": NEWS_FETCH_INTERVAL_MINUTES * 60 - 10,  # Expire before next run
        }
    },
}

