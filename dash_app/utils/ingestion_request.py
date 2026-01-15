import requests

from utils.config import FASTAPI_BASE_URL

def ingestion_request(provider: str, search_term: str, search: str, limit: int = 10):
    """
    Send an ingestion request to FastAPI backend

    provider: provider to be queried, e.g. 'polymarket'
    search_term: string identifier to be queried, e.g. an api specific event id or keyword
    search: search type, "exact" or "keyword

    """
    
    if search == 'exact':
        search_dict = {
            "kind": "exact",
        }
    elif search == 'keyword':
        search_dict = {
            "kind": "keyword",
            "limit": limit
        }
    else:
        raise ValueError("search must be 'exact' or 'keyword'")

    # Construct full request payload
    payload = {
        "provider": provider,
        "search_term": search_term,
        "search": search_dict
    }

    print(payload)

    ingestion = requests.post(f"{FASTAPI_BASE_URL}/ingestion", json=payload)
    ingestion.raise_for_status()

    return ingestion.json()
