"""
This module creates a base model for data ingestion
"""

from pydantic import BaseModel
from datetime import date

from typing import Literal, Union

from app.fastapi.schemas.intent import SearchIntent
from app.fastapi.schemas.providers import KalshiConfig, PolymarketConfig

class IngestionBase(BaseModel):
    provider : str
    intent : SearchIntent
    query : str

class KalshiIngestion(IngestionBase):
    provider : Literal['kalshi'] # type: ignore
    config: type[KalshiConfig] = KalshiConfig

class PolymarketIngestion(IngestionBase):
    provider : Literal['polymarket'] # type: ignore
    config: type[PolymarketConfig] = PolymarketConfig

IngestionRequest = Union[
    KalshiIngestion,
    PolymarketIngestion]




    