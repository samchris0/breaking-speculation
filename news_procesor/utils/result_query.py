import requests
from typing import Dict, Tuple

from utils.config import FASTAPI_BASE_URL

def result_query(task_id: str) -> Dict:
    
    results = requests.get(f"{FASTAPI_BASE_URL}/ingestion/{task_id}")
    
    results.raise_for_status()

    results = results.json()
    
    return results
