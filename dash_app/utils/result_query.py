import requests

from utils.config import FASTAPI_BASE_URL

def result_query(task_id):
    
    results = requests.post(f"{FASTAPI_BASE_URL}/{task_id}")
    results.raise_for_status()

    results = results.json()

    if results.status == 'success':
        return results.data