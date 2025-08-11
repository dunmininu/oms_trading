"""
Events and webhooks API endpoints.
"""

from ninja import Router
from typing import List, Dict, Any
from django.http import HttpRequest

router = Router()


@router.get("/", tags=["Events"])
def list_events(request: HttpRequest) -> Dict[str, Any]:
    """List available events."""
    return {
        "events": [
            "order.created",
            "order.filled",
            "order.cancelled",
            "position.changed",
            "broker.connected",
            "broker.disconnected"
        ]
    }


@router.post("/webhook", tags=["Events"])
def create_webhook(request: HttpRequest) -> Dict[str, Any]:
    """Create a new webhook subscription."""
    # TODO: Implement webhook creation
    return {"message": "Webhook creation not yet implemented"}


@router.get("/webhooks", tags=["Events"])
def list_webhooks(request: HttpRequest) -> Dict[str, Any]:
    """List configured webhooks."""
    # TODO: Implement webhook listing
    return {"webhooks": []}
