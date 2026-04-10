"""
Events and webhooks API endpoints.
"""

from typing import Any

from django.http import HttpRequest
from ninja import Router

router = Router()


@router.get("/", tags=["Events"])
def list_events(request: HttpRequest) -> dict[str, Any]:
    """List available events."""
    return {
        "events": [
            "order.created",
            "order.filled",
            "order.cancelled",
            "position.changed",
            "broker.connected",
            "broker.disconnected",
        ]
    }


@router.post("/webhook", tags=["Events"])
def create_webhook(request: HttpRequest) -> dict[str, Any]:
    """Create a new webhook subscription."""
    # TODO: Implement webhook creation
    return {"message": "Webhook creation not yet implemented"}


@router.get("/webhooks", tags=["Events"])
def list_webhooks(request: HttpRequest) -> dict[str, Any]:
    """List configured webhooks."""
    # TODO: Implement webhook listing
    return {"webhooks": []}
