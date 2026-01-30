import logging
from celery.utils.log import get_task_logger

def setup_root_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

def get_logger(name):
    setup_root_logger()
    return get_task_logger(name)