"""
WebSocket-based SDK for interacting with the Deriv API.
"""

import json
import logging
from collections.abc import Callable

import websockets

logger = logging.getLogger(__name__)


class DerivClient:
    """
    Client for Deriv API (Synthetic Indices).
    """

    URL = "wss://ws.binaryws.com/websockets/v3?app_id=1089"  # Default demo app_id

    def __init__(self, token: str, app_id: str | None = None):
        self.token = token
        if app_id:
            self.URL = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        self.ws = None
        self.is_authenticated = False
        self._callbacks: dict[str, Callable] = {}

    async def connect(self):
        """Connect to Deriv WebSocket."""
        try:
            self.ws = await websockets.connect(self.URL)
            logger.info("Connected to Deriv WebSocket")
            return await self.authorize()
        except Exception as e:
            logger.error(f"Deriv connection error: {e}")
            return False

    async def authorize(self):
        """Authorize the connection with the API token."""
        request = {"authorize": self.token}
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv Auth Error: {data['error']['message']}")
            return False

        self.is_authenticated = True
        logger.info(f"Deriv Authorized: {data['authorize']['email']}")
        return True

    async def get_tick_stream(self, symbol: str, callback: Callable):
        """Subscribe to a real-time tick stream."""
        request = {"ticks": symbol}
        await self.ws.send(json.dumps(request))

        while self.is_authenticated:
            response = await self.ws.recv()
            data = json.loads(response)
            if "tick" in data:
                await callback(data["tick"])

    async def place_trade(self, symbol: str, amount: float, contract_type: str):
        """
        Place a trade on Deriv.
        contract_type: 'CALL' or 'PUT'
        """
        # Simplified: buy a 1-minute duration contract
        request = {
            "buy": 1,
            "price": amount,
            "parameters": {
                "amount": amount,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "m",
                "symbol": symbol,
            },
        }
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.is_authenticated = False
