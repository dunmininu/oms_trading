"""
Utilities for creating IB orders.
"""

<<<<<<< HEAD
from decimal import Decimal
from ib_insync import MarketOrder, LimitOrder, StopOrder, StopLimitOrder, Order
=======
from ib_insync import LimitOrder, MarketOrder, StopLimitOrder, StopOrder

>>>>>>> origin/main

def create_market_order(side: str, quantity: float) -> MarketOrder:
    """Create a market order."""
    return MarketOrder(side, quantity)

<<<<<<< HEAD
=======

>>>>>>> origin/main
def create_limit_order(side: str, quantity: float, limit_price: float) -> LimitOrder:
    """Create a limit order."""
    return LimitOrder(side, quantity, limit_price)

<<<<<<< HEAD
=======

>>>>>>> origin/main
def create_stop_order(side: str, quantity: float, stop_price: float) -> StopOrder:
    """Create a stop order."""
    return StopOrder(side, quantity, stop_price)

<<<<<<< HEAD
def create_stop_limit_order(side: str, quantity: float, limit_price: float, stop_price: float) -> StopLimitOrder:
=======

def create_stop_limit_order(
    side: str, quantity: float, limit_price: float, stop_price: float
) -> StopLimitOrder:
>>>>>>> origin/main
    """Create a stop limit order."""
    return StopLimitOrder(side, quantity, limit_price, stop_price)
