"""
This module creates an axis to the polymorphic ingestion request allowing us to specify the "intent" of this
search. We can specify a search to be exact, in which case a specific market or event will be searched for.
Alternatively, we can specify a search to be keyword, in which case the provider will be queried for the specified
keyword and markets will be returned up to the specified limit.
"""

from pydantic import BaseModel
from typing import Literal, Optional

class ExactIntent(BaseModel):
    intent : Literal['exact']
    event_id : str

class KeywordIntent(BaseModel):
    intent : Literal['keyword']
    query : str
    limit : Optional[int] = 10

SearchIntent = ExactIntent | KeywordIntent