"""
Utilities for creating and qualifying IB contracts.
"""

from ib_insync import Contract, Stock, Forex, Crypto, Option, Future

def create_forex_contract(symbol: str, currency: str = 'USD', exchange: str = 'IDEALPRO') -> Forex:
    """Create a Forex contract."""
    return Forex(symbol, currency=currency, exchange=exchange)

def create_crypto_contract(symbol: str, currency: str = 'USD', exchange: str = 'PAXOS') -> Crypto:
    """Create a Crypto contract."""
    return Crypto(symbol, currency=currency, exchange=exchange)

def create_stock_contract(symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> Stock:
    """Create a Stock contract."""
    return Stock(symbol, exchange, currency)

def create_gbpjpy_contract() -> Forex:
    """Create a GBPJPY Forex contract."""
    return create_forex_contract('GBP', 'JPY')

def create_btcusd_contract() -> Crypto:
    """Create a BTCUSD Crypto contract."""
    return create_crypto_contract('BTC', 'USD')
