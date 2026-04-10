"""
High-speed Redis cache for market data ticks and bars.
"""

import json
import logging
import time
from typing import Any

from django.core.cache import cache
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)


class MarketDataCache:
    """Redis-based cache for low-latency market data access."""

    @classmethod
    def push_tick(cls, symbol: str, price: float, volume: int):
        """Push a real-time tick to a Redis Sorted Set (Time-ordered)."""
        try:
            redis = get_redis_connection("default")
            timestamp = time.time()
            tick_data = {"p": price, "v": volume, "t": timestamp}
            key = f"ticks:{symbol.upper()}"
            redis.zadd(key, {json.dumps(tick_data): timestamp})
            redis.zremrangebyrank(key, 0, -1001)
        except (NotImplementedError, Exception):
            # Fallback for LocMem during testing
            key = f"ticks:{symbol.upper()}"
            current = cache.get(key, [])
            current.append({"p": price, "v": volume, "t": time.time()})
            cache.set(key, current[-1000:])

    @classmethod
    def get_recent_ticks(cls, symbol: str, count: int = 100) -> list[dict[str, Any]]:
        """Retrieve most recent ticks from Redis."""
        try:
            redis = get_redis_connection("default")
            key = f"ticks:{symbol.upper()}"
            data = redis.zrevrange(key, 0, count - 1)
            return [json.loads(d) for d in data]
        except (NotImplementedError, Exception):
            key = f"ticks:{symbol.upper()}"
            data = cache.get(key, [])
            return list(reversed(data))[:count]

    @classmethod
    def update_bar(cls, symbol: str, interval: str, bar_data: dict[str, Any]):
        """Update/Store the most recent candle in Redis."""
        key = f"bar:{symbol.upper()}:{interval}"
        # Set with 24h expiry
        cache.set(key, bar_data, timeout=86400)

    @classmethod
    def get_latest_bar(cls, symbol: str, interval: str) -> dict[str, Any] | None:
        """Get the latest bar from Redis."""
        key = f"bar:{symbol.upper()}:{interval}"
        return cache.get(key)
