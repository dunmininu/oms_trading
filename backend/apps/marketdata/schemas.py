"""
Market Data schemas for Django Ninja API.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ninja import Field, Schema
from pydantic import validator

from apps.api.schemas import BaseFilterSchema, DateRangeFilterSchema

# =============================================================================
# MARKET DATA SCHEMAS
# =============================================================================


class MarketDataResponseSchema(Schema):
    """Market data response schema."""

    id: str = Field(description="Market data ID")
    tenant_id: str = Field(description="Tenant ID")
    instrument_id: str = Field(description="Instrument ID")

    # Price data
    last_price: Decimal | None = Field(description="Last traded price")
    bid_price: Decimal | None = Field(description="Current bid price")
    ask_price: Decimal | None = Field(description="Current ask price")
    mid_price: Decimal | None = Field(description="Mid price (bid + ask) / 2")

    # Volume and liquidity
    volume: int | None = Field(description="Trading volume")
    bid_size: int | None = Field(description="Bid size")
    ask_size: int | None = Field(description="Ask size")

    # Market indicators
    high_price: Decimal | None = Field(description="High price for the period")
    low_price: Decimal | None = Field(description="Low price for the period")
    open_price: Decimal | None = Field(description="Open price for the period")
    close_price: Decimal | None = Field(description="Close price for the period")

    # Option-specific data
    implied_volatility: Decimal | None = Field(description="Implied volatility")
    delta: Decimal | None = Field(description="Option delta")
    gamma: Decimal | None = Field(description="Option gamma")
    theta: Decimal | None = Field(description="Option theta")
    vega: Decimal | None = Field(description="Option vega")

    # Timestamps
    timestamp: datetime = Field(description="Data timestamp")
    last_updated: datetime = Field(description="Last update timestamp")

    # Data quality
    data_source: str = Field(description="Data source")
    is_delayed: bool = Field(description="Whether data is delayed")
    delay_minutes: int | None = Field(description="Delay in minutes")

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")


class MarketDataFilterSchema(BaseFilterSchema):
    """Market data filter schema."""

    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    data_source: str | None = Field(description="Filter by data source")
    is_delayed: bool | None = Field(description="Filter by delay status")
    min_price: Decimal | None = Field(description="Minimum price filter")
    max_price: Decimal | None = Field(description="Maximum price filter")


class HistoricalDataRequestSchema(Schema):
    """Historical data request schema."""

    instrument_symbol: str = Field(description="Trading symbol")
    start_date: date = Field(description="Start date")
    end_date: date = Field(description="End date")
    interval: str = Field(description="Data interval (1m, 5m, 1h, 1d, etc.)")
    data_source: str | None = Field(description="Data source")

    @validator("end_date")
    def validate_date_range(self, v, values):
        """Validate end date is after start date."""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class HistoricalDataResponseSchema(Schema):
    """Historical data response schema."""

    instrument_symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Data interval")
    data_source: str = Field(description="Data source")

    # Data points
    data_points: list[dict[str, Any]] = Field(description="Historical data points")

    # Summary
    total_points: int = Field(description="Total number of data points")
    start_date: date = Field(description="Start date")
    end_date: date = Field(description="End date")

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")


# =============================================================================
# SUBSCRIPTION SCHEMAS
# =============================================================================


class SubscriptionCreateSchema(Schema):
    """Market data subscription creation schema."""

    instrument_symbols: list[str] = Field(
        description="List of instrument symbols to subscribe to"
    )
    data_types: list[str] = Field(description="Types of data to subscribe to")
    update_frequency: str = Field(
        description="Update frequency (real-time, 1s, 5s, etc.)"
    )
    delivery_method: str = Field(description="Delivery method (SSE, WebSocket, etc.)")

    # Filtering options
    price_threshold: Decimal | None = Field(
        description="Price change threshold for updates"
    )
    volume_threshold: int | None = Field(
        description="Volume change threshold for updates"
    )

    # Delivery options
    callback_url: str | None = Field(description="Webhook callback URL")
    include_metadata: bool = Field(
        description="Whether to include metadata", default=True
    )

    # Metadata
    notes: str | None = Field(description="Subscription notes")
    metadata: dict[str, Any] | None = Field(description="Additional metadata")


class SubscriptionUpdateSchema(Schema):
    """Market data subscription update schema."""

    instrument_symbols: list[str] | None = Field(
        description="List of instrument symbols"
    )
    data_types: list[str] | None = Field(description="Types of data")
    update_frequency: str | None = Field(description="Update frequency")
    delivery_method: str | None = Field(description="Delivery method")

    # Filtering options
    price_threshold: Decimal | None = Field(description="Price change threshold")
    volume_threshold: int | None = Field(description="Volume change threshold")

    # Delivery options
    callback_url: str | None = Field(description="Webhook callback URL")
    include_metadata: bool | None = Field(description="Whether to include metadata")

    # Status
    is_active: bool | None = Field(description="Whether subscription is active")

    # Metadata
    notes: str | None = Field(description="Subscription notes")
    metadata: dict[str, Any] | None = Field(description="Additional metadata")


class SubscriptionResponseSchema(Schema):
    """Market data subscription response schema."""

    id: str = Field(description="Subscription ID")
    tenant_id: str = Field(description="Tenant ID")
    user_id: str = Field(description="User ID")

    # Subscription details
    instrument_symbols: list[str] = Field(description="Subscribed instrument symbols")
    data_types: list[str] = Field(description="Subscribed data types")
    update_frequency: str = Field(description="Update frequency")
    delivery_method: str = Field(description="Delivery method")

    # Filtering options
    price_threshold: Decimal | None = Field(description="Price change threshold")
    volume_threshold: int | None = Field(description="Volume change threshold")

    # Delivery options
    callback_url: str | None = Field(description="Webhook callback URL")
    include_metadata: bool = Field(description="Whether metadata is included")

    # Status
    is_active: bool = Field(description="Whether subscription is active")
    last_heartbeat: datetime | None = Field(description="Last heartbeat timestamp")

    # Statistics
    total_updates: int = Field(description="Total number of updates sent")
    last_update: datetime | None = Field(description="Last update timestamp")
    error_count: int = Field(description="Number of delivery errors")

    # Metadata
    notes: str | None = Field(description="Subscription notes")
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SubscriptionFilterSchema(BaseFilterSchema):
    """Subscription filter schema."""

    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    data_type: str | None = Field(description="Filter by data type")
    delivery_method: str | None = Field(description="Filter by delivery method")
    is_active: bool | None = Field(description="Filter by active status")
    user_id: str | None = Field(description="Filter by user")


# =============================================================================
# TICK DATA SCHEMAS
# =============================================================================


class TickDataResponseSchema(Schema):
    """Tick data response schema."""

    id: str = Field(description="Tick data ID")
    tenant_id: str = Field(description="Tenant ID")
    instrument_id: str = Field(description="Instrument ID")

    # Tick details
    tick_type: str = Field(description="Type of tick (bid, ask, trade, etc.)")
    price: Decimal = Field(description="Tick price")
    size: int = Field(description="Tick size")

    # Market context
    bid_price: Decimal | None = Field(description="Current bid price")
    ask_price: Decimal | None = Field(description="Current ask price")
    last_price: Decimal | None = Field(description="Last traded price")

    # Timestamps
    timestamp: datetime = Field(description="Tick timestamp")
    exchange_timestamp: datetime | None = Field(description="Exchange timestamp")

    # Data quality
    data_source: str = Field(description="Data source")
    is_delayed: bool = Field(description="Whether data is delayed")

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")


class TickDataFilterSchema(DateRangeFilterSchema):
    """Tick data filter schema."""

    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    tick_type: str | None = Field(description="Filter by tick type")
    data_source: str | None = Field(description="Filter by data source")
    min_price: Decimal | None = Field(description="Minimum price filter")
    max_price: Decimal | None = Field(description="Maximum price filter")


# =============================================================================
# MARKET DATA SNAPSHOT SCHEMAS
# =============================================================================


class MarketDataSnapshotResponseSchema(Schema):
    """Market data snapshot response schema."""

    id: str = Field(description="Snapshot ID")
    tenant_id: str = Field(description="Tenant ID")

    # Snapshot details
    snapshot_time: datetime = Field(description="Snapshot timestamp")
    data_source: str = Field(description="Data source")

    # Market summary
    total_instruments: int = Field(description="Total number of instruments")
    active_instruments: int = Field(description="Number of active instruments")

    # Price summary
    price_updates: int = Field(description="Number of price updates")
    volume_updates: int = Field(description="Number of volume updates")

    # Data quality
    delayed_data_count: int = Field(description="Number of delayed data points")
    error_count: int = Field(description="Number of data errors")

    # Performance
    average_latency_ms: float | None = Field(
        description="Average data latency in milliseconds"
    )
    max_latency_ms: float | None = Field(
        description="Maximum data latency in milliseconds"
    )

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class MarketDataSnapshotFilterSchema(DateRangeFilterSchema):
    """Market data snapshot filter schema."""

    data_source: str | None = Field(description="Filter by data source")
    min_instruments: int | None = Field(description="Minimum number of instruments")
    max_instruments: int | None = Field(description="Maximum number of instruments")


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================


class BulkSubscriptionCreateSchema(Schema):
    """Bulk subscription creation schema."""

    subscriptions: list[SubscriptionCreateSchema] = Field(
        description="List of subscriptions to create"
    )
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkSubscriptionResponseSchema(Schema):
    """Bulk subscription response schema."""

    accepted: list[SubscriptionResponseSchema] = Field(
        description="Successfully created subscriptions"
    )
    rejected: list[dict[str, Any]] = Field(
        description="Failed subscriptions with error details"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class MarketDataListResponseSchema(Schema):
    """Market data list response schema."""

    market_data: list[MarketDataResponseSchema] = Field(
        description="List of market data"
    )
    total_count: int = Field(description="Total number of data points")
    has_next: bool = Field(description="Whether there are more data points")


class SubscriptionListResponseSchema(Schema):
    """Subscription list response schema."""

    subscriptions: list[SubscriptionResponseSchema] = Field(
        description="List of subscriptions"
    )
    total_count: int = Field(description="Total number of subscriptions")
    has_next: bool = Field(description="Whether there are more subscriptions")


class TickDataListResponseSchema(Schema):
    """Tick data list response schema."""

    ticks: list[TickDataResponseSchema] = Field(description="List of tick data")
    total_count: int = Field(description="Total number of ticks")
    has_next: bool = Field(description="Whether there are more ticks")


class MarketDataSnapshotListResponseSchema(Schema):
    """Market data snapshot list response schema."""

    snapshots: list[MarketDataSnapshotResponseSchema] = Field(
        description="List of snapshots"
    )
    total_count: int = Field(description="Total number of snapshots")
    has_next: bool = Field(description="Whether there are more snapshots")
