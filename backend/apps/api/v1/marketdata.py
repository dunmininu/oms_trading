"""
Market data API endpoints.
"""

from typing import Any

from django.http import HttpRequest
from ninja import Router

router = Router()


@router.get("/", tags=["Market Data"])
def list_symbols(request: HttpRequest) -> dict[str, Any]:
    """List available market symbols."""
    # TODO: Implement symbol listing
    return {"symbols": []}


@router.get("/quotes/{symbol}", tags=["Market Data"])
def get_quote(request: HttpRequest, symbol: str) -> dict[str, Any]:
    """Get current quote for a symbol."""
    # TODO: Implement quote retrieval
    return {"symbol": symbol, "quote": "Not yet implemented"}


@router.get("/bars/{symbol}", tags=["Market Data"])
def get_bars(request: HttpRequest, symbol: str) -> dict[str, Any]:
    """Get historical bars for a symbol."""
    # TODO: Implement historical data retrieval
    return {"symbol": symbol, "bars": []}
