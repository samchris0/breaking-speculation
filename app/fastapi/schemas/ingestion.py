"""
This module creates a base model for data ingestion
"""

from pydantic import BaseModel
from datetime import date

from typing import Literal, Union

from intent import SearchIntent
from providers import KalshiConfig, PolymarketConfig

class IngestionBase(BaseModel):
    provider : str
    intent : SearchIntent
    query : str

class KalshiIngestion(IngestionBase):
    provider : Literal['kalshi'] # type: ignore
    config = KalshiConfig

class PolymarketIngestion(IngestionBase):
    provider : Literal['polymarket'] # type: ignore
    config = PolymarketConfig

IngestionRequest = Union[
    KalshiIngestion,
    PolymarketIngestion]




    