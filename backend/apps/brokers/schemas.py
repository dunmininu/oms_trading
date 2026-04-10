"""
Broker schemas for Django Ninja API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from ninja import Schema


class BrokerConnectionSchema(Schema):
    """Schema for broker connection."""

    id: str | None = None
    broker_id: str
    connection_type: str
    status: str
    host: str
    port: int
    client_id: int
    is_paper_trading: bool = False
    last_heartbeat: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BrokerConnectionCreateSchema(Schema):
    """Schema for creating broker connection."""

    broker_id: str
    connection_type: str
    host: str
    port: int
    client_id: int
    is_paper_trading: bool = False
    credentials: dict[str, Any] | None = None


class BrokerConnectionUpdateSchema(Schema):
    """Schema for updating broker connection."""

    host: str | None = None
    port: int | None = None
    client_id: int | None = None
    is_paper_trading: bool | None = None
    credentials: dict[str, Any] | None = None


class BrokerAccountSchema(Schema):
    """Schema for broker account."""

    id: str | None = None
    broker_id: str
    account_number: str
    account_type: str
    currency: str
    balance: Decimal | None = None
    buying_power: Decimal | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BrokerAccountCreateSchema(Schema):
    """Schema for creating broker account."""

    broker_id: str
    account_number: str
    account_type: str
    currency: str
    credentials: dict[str, Any] | None = None


class BrokerLogSchema(Schema):
    """Schema for broker log entry."""

    id: str | None = None
    broker_id: str
    level: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime | None = None


class BrokerCreateSchema(Schema):
    """Schema for creating a broker."""

    name: str
    broker_type: str
    description: str | None = None
    is_active: bool = True
    config: dict[str, Any] | None = None


class BrokerUpdateSchema(Schema):
    """Schema for updating a broker."""

    name: str | None = None
    broker_type: str | None = None
    description: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class BrokerResponseSchema(Schema):
    """Schema for broker response."""

    id: str
    name: str
    broker_type: str
    description: str | None = None
    is_active: bool
    config: dict[str, Any] | None = None
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class BrokerAccountUpdateSchema(Schema):
    """Schema for updating broker account."""

    account_type: str | None = None
    currency: str | None = None
    credentials: dict[str, Any] | None = None
    is_active: bool | None = None


class BrokerAccountResponseSchema(Schema):
    """Schema for broker account response."""

    id: str
    broker_id: str
    account_number: str
    account_type: str
    currency: str
    balance: Decimal | None = None
    buying_power: Decimal | None = None
    is_active: bool
    tenant_id: str
    created_at: datetime
    updated_at: datetime
