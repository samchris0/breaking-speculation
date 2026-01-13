"""

"""

from pydantic import BaseModel
from typing import Literal, Optional

class KalshiConfig(BaseModel):
    base_url : str 


class PolymarketConfig(BaseModel):
    base_url : str = "https://gamma-api.polymarket.com"
    
