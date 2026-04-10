"""
Trading strategies API endpoints.
"""

from typing import Any

from django.http import HttpRequest
from ninja import Router

router = Router()


@router.get("/", tags=["Strategies"])
def list_strategies(request: HttpRequest) -> dict[str, Any]:
    """List all trading strategies."""
    # TODO: Implement strategy listing
    return {"strategies": []}


@router.post("/", tags=["Strategies"])
def create_strategy(request: HttpRequest) -> dict[str, Any]:
    """Create a new trading strategy."""
    # TODO: Implement strategy creation
    return {"message": "Strategy creation not yet implemented"}


@router.get("/{strategy_id}", tags=["Strategies"])
def get_strategy(request: HttpRequest, strategy_id: int) -> dict[str, Any]:
    """Get a specific strategy."""
    # TODO: Implement strategy retrieval
    return {"strategy_id": strategy_id, "strategy": "Not yet implemented"}
