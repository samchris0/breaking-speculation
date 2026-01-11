"""
This module creates a base model for data ingestion
"""

from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from app.fastapi.schemas.intent import SearchType
from app.fastapi.schemas.providers import KalshiConfig, PolymarketConfig

class IngestionBase(BaseModel):
    provider : str
    search : SearchType
    query : str

class KalshiIngestion(IngestionBase):
    provider : Literal['kalshi'] # type: ignore
    config: type[KalshiConfig] = KalshiConfig

class PolymarketIngestion(IngestionBase):
    provider : Literal['polymarket'] # type: ignore
    config: type[PolymarketConfig] = PolymarketConfig

IngestionRequest = Annotated[
        KalshiIngestion | PolymarketIngestion,
        Field(discriminator="provider")
]
   