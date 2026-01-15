"""
This module creates a base model for data ingestion
"""

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from fastapi_app.schemas.intent import SearchType
from fastapi_app.schemas.providers import KalshiConfig, PolymarketConfig

class IngestionBase(BaseModel):
    provider : str
    search_term : str
    search : SearchType

class KalshiIngestion(IngestionBase):
    provider : Literal['kalshi'] # type: ignore
    config: KalshiConfig = KalshiConfig()

class PolymarketIngestion(IngestionBase):
    provider : Literal['polymarket'] # type: ignore
    config: PolymarketConfig = PolymarketConfig()

IngestionRequest = Annotated[
        Union[KalshiIngestion, PolymarketIngestion],
        Field(discriminator="provider")
]
   