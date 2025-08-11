"""
Broker schemas for Django Ninja API.
"""

from ninja import Schema
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class BrokerConnectionSchema(Schema):
    """Schema for broker connection."""
    id: Optional[str] = None
    broker_id: str
    connection_type: str
    status: str
    host: str
    port: int
    client_id: int
    is_paper_trading: bool = False
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BrokerConnectionCreateSchema(Schema):
    """Schema for creating broker connection."""
    broker_id: str
    connection_type: str
    host: str
    port: int
    client_id: int
    is_paper_trading: bool = False
    credentials: Optional[Dict[str, Any]] = None


class BrokerConnectionUpdateSchema(Schema):
    """Schema for updating broker connection."""
    host: Optional[str] = None
    port: Optional[int] = None
    client_id: Optional[int] = None
    is_paper_trading: Optional[bool] = None
    credentials: Optional[Dict[str, Any]] = None


class BrokerAccountSchema(Schema):
    """Schema for broker account."""
    id: Optional[str] = None
    broker_id: str
    account_number: str
    account_type: str
    currency: str
    balance: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BrokerAccountCreateSchema(Schema):
    """Schema for creating broker account."""
    broker_id: str
    account_number: str
    account_type: str
    currency: str
    credentials: Optional[Dict[str, Any]] = None


class BrokerLogSchema(Schema):
    """Schema for broker log entry."""
    id: Optional[str] = None
    broker_id: str
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class BrokerCreateSchema(Schema):
    """Schema for creating a broker."""
    name: str
    broker_type: str
    description: Optional[str] = None
    is_active: bool = True
    config: Optional[Dict[str, Any]] = None


class BrokerUpdateSchema(Schema):
    """Schema for updating a broker."""
    name: Optional[str] = None
    broker_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class BrokerResponseSchema(Schema):
    """Schema for broker response."""
    id: str
    name: str
    broker_type: str
    description: Optional[str] = None
    is_active: bool
    config: Optional[Dict[str, Any]] = None
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class BrokerAccountUpdateSchema(Schema):
    """Schema for updating broker account."""
    account_type: Optional[str] = None
    currency: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class BrokerAccountResponseSchema(Schema):
    """Schema for broker account response."""
    id: str
    broker_id: str
    account_number: str
    account_type: str
    currency: str
    balance: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    is_active: bool
    tenant_id: str
    created_at: datetime
    updated_at: datetime
