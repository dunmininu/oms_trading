"""
WebSocket-based SDK for interacting with the Deriv API.
"""

<<<<<<< HEAD
import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

=======
import json
import logging
from collections.abc import Callable

import websockets

logger = logging.getLogger(__name__)


>>>>>>> origin/main
class DerivClient:
    """
    Client for Deriv API (Synthetic Indices).
    """
<<<<<<< HEAD

    URL = "wss://ws.binaryws.com/websockets/v3?app_id=1089" # Default demo app_id

    def __init__(self, token: str, app_id: Optional[str] = None):
=======

    URL = "wss://ws.binaryws.com/websockets/v3?app_id=1089"  # Default demo app_id

    def __init__(self, token: str, app_id: str | None = None):
>>>>>>> origin/main
        self.token = token
        if app_id:
            self.URL = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        self.ws = None
        self.is_authenticated = False
<<<<<<< HEAD
        self._callbacks: Dict[str, Callable] = {}

    async def connect(self):
        """Connect to Deriv WebSocket."""
        try:
            self.ws = await websockets.connect(self.URL)
            logger.info("Connected to Deriv WebSocket")
=======
        self._lock = None
        self._callbacks: dict[str, Callable] = {}

    @property
    def lock(self):
        """Lazy initialization of lock to ensure it belongs to the current event loop."""
        import asyncio

        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @property
    def is_connected(self) -> bool:
        return self.ws is not None and getattr(self.ws, "open", False)

    async def connect(self):
        """Connect to Deriv WebSocket."""
        # Clean up stale ws if it exists
        if self.ws and not getattr(self.ws, "open", False):
            await self.disconnect()

        try:
            if not self.ws:
                self.ws = await websockets.connect(self.URL)
                logger.info("TCP Connection Established with Deriv")

>>>>>>> origin/main
            return await self.authorize()
        except Exception as e:
            logger.error(f"Deriv connection error: {e}")
            return False

    async def authorize(self):
<<<<<<< HEAD
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
=======
        """Authorize the connection with the API token (Loop-safe Lock protected)."""
        async with self.lock:
            if self.is_authenticated and self.is_connected:
                return True

            if not self.is_connected:
                return False

            request = {"authorize": self.token}
            await self.ws.send(json.dumps(request))
            response = await self.ws.recv()
            data = json.loads(response)

            if "error" in data:
                logger.error(
                    f"Deriv Auth Error: {data['error']['message']} (Code: {data['error'].get('code')})"
                )
                self.is_authenticated = False
                return False

            self.is_authenticated = True
            auth_data = data["authorize"]
            self.accounts = auth_data.get("account_list", [])
            self.currency = auth_data.get("currency", "USD")

            # Critical: Allow server a moment to propagate authorization state across its cluster
            import asyncio

            await asyncio.sleep(0.5)

            logger.info(f"Deriv Session Authorized: {auth_data['email']}")
            return True

    async def ping(self):
        """Send a heartbeat ping to keep the WebSocket alive."""
        if not self.is_connected:
            return False

        try:
            request = {"ping": 1}
            await self.ws.send(json.dumps(request))
            # Optional: wait for response periodically or just fire and forget if socket layer handles it
            return True
        except Exception as e:
            logger.warning(f"Deriv Heartbeat Failed: {e}")
            self.is_authenticated = False
            return False
>>>>>>> origin/main

    async def get_tick_stream(self, symbol: str, callback: Callable):
        """Subscribe to a real-time tick stream."""
        request = {"ticks": symbol}
        await self.ws.send(json.dumps(request))
<<<<<<< HEAD

=======

>>>>>>> origin/main
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
<<<<<<< HEAD
                "symbol": symbol
            }
=======
                "symbol": symbol,
            },
>>>>>>> origin/main
        }
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)

<<<<<<< HEAD
=======
    async def get_active_symbols(self):
        """Fetch all actively traded synthetic symbols from Deriv."""
        request = {"active_symbols": "brief", "product_type": "basic"}
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv Active Symbols Error: {data['error']['message']}")
            return []

        return data.get("active_symbols", [])

    async def get_historical_candles(
        self, symbol: str, count: int = 1000, granularity: int = 900
    ):
        """
        Fetch historical bars using the 'ticks_history' Deriv WebSocket API.
        Granularity defaults to 900 seconds (15 minutes).
        """
        request = {
            "ticks_history": symbol,
            "style": "candles",
            "end": "latest",
            "count": count,
            "granularity": granularity,
        }
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv History Error: {data['error']['message']}")
            return []

        return data.get("candles", [])

    async def get_balances(self) -> dict:
        """Fetch live balances for all authorized accounts."""
        # Auto-reconnect if the connection silently dropped
        if not self.is_connected:
            connected = await self.connect()
            if not connected:
                logger.error(
                    "Deriv get_balances failed: Cannot awaken dead connection."
                )
                return {}

        request = {"balance": 1}
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv Balance Error: {data['error']['message']}")
            return {}

        balance_data = data.get("balance", {})
        if "accounts" in balance_data:
            return balance_data["accounts"]

        # Fallback if specific account
        if "loginid" in balance_data:
            return {
                balance_data["loginid"]: {"balance": balance_data.get("balance", 0)}
            }

        return {}

    async def get_portfolio(self):
        """Fetch open contracts from the authenticated account."""
        if not self.is_connected:
            await self.connect()

        request = {"portfolio": 1}
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv Portfolio Error: {data['error']['message']}")
            return []

        return data.get("portfolio", {}).get("contracts", [])

    async def get_statement(self, limit: int = 50):
        """Fetch transaction history from the authenticated account."""
        if not self.is_connected:
            await self.connect()

        request = {"statement": 1, "description": 1, "limit": limit}
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            logger.error(f"Deriv Statement Error: {data['error']['message']}")
            return []

        return data.get("statement", {}).get("transactions", [])

>>>>>>> origin/main
    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.is_authenticated = False
