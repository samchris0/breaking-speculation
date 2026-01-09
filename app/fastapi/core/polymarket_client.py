import httpx

GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
CLOB_BASE_URL = "https://clob.polymarket.com"

class PolymarketClient:
    def __init__(self):
        self.gamma = httpx.AsyncClient(
            base_url=GAMMA_BASE_URL,
            timeout=10.0,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            )
        )
        self.clob = httpx.AsyncClient(
            base_url=CLOB_BASE_URL,
            timeout=10.0
        )

    async def close(self):
        await self.gamma.aclose()
        await self.clob.aclose()

class PolymarketError(Exception):
    """Base class for Polymarket ingestion exceptions."""
    pass

class PolymarketRateLimit(PolymarketError):
    """Raised when Polymarket API returns 429 Too Many Requests."""
    pass

class PolymarketUnavailable(PolymarketError):
    """Raised when Polymarket API is unavailable or times out."""
    pass