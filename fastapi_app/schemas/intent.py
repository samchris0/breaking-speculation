"""
This module creates an axis to the polymorphic ingestion request allowing us to specify the "intent" of this
search. We can specify a search to be exact, in which case a specific market or event will be searched for.
Alternatively, we can specify a search to be keyword, in which case the provider will be queried for the specified
keyword and markets will be returned up to the specified limit.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated

class ExactSearch(BaseModel):
    kind : Literal['exact']

class KeywordSearch(BaseModel):
    kind : Literal['keyword']
    limit : Optional[int] = 30

SearchType = Annotated[
            ExactSearch | KeywordSearch,
            Field(discriminator="kind")
            ]
