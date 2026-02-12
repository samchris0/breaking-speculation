import requests

from utils.config import FASTAPI_BASE_URL

def ingestion_request(search_term: str, limit: int = 10):
    """
    Send an ingestion request to FastAPI backend

    provider: provider to be queried, e.g. 'polymarket'
    search_term: string identifier to be queried, e.g. an api specific event id or keyword
    search: search type, "exact" or "keyword

    """
    
    search_dict = {
        "kind": "keyword",
        "limit": limit
    }

    # Construct full request payload
    payload = {
        "provider": 'polymarket',
        "search_term": search_term,
        "search": search_dict
    }

    ingestion = requests.post(f"{FASTAPI_BASE_URL}/ingestion", json=payload)
    ingestion.raise_for_status()

    return ingestion.json()
