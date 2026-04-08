"""
Utilities for creating IB orders.
"""

from decimal import Decimal
from ib_insync import MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order

def create_market_order(side: str, quantity: float) -> MarketOrder:
    """Create a market order."""
    return MarketOrder(side, quantity)

def create_limit_order(side: str, quantity: float, limit_price: float) -> LimitOrder:
    """Create a limit order."""
    return LimitOrder(side, quantity, limit_price)

def create_stop_order(side: str, quantity: float, stop_price: float) -> StopOrder:
    """Create a stop order."""
    return StopOrder(side, quantity, stop_price)

def create_stop_limit_order(side: str, quantity: float, limit_price: float, stop_price: float) -> StopLimitOrder:
    """Create a stop limit order."""
    return StopLimitOrder(side, quantity, limit_price, stop_price)
