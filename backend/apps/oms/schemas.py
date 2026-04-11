"""
OMS schemas for Django Ninja API.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ninja import Field, Schema
from pydantic import validator

from apps.api.schemas import BaseFilterSchema, DateRangeFilterSchema, StatusFilterSchema

# =============================================================================
# INSTRUMENT SCHEMAS
# =============================================================================


class InstrumentResponseSchema(Schema):
    """Instrument response schema."""

    id: str = Field(description="Instrument ID")
    symbol: str = Field(description="Trading symbol")
    name: str = Field(description="Instrument name")
    instrument_type: str = Field(description="Type of instrument")
    exchange: str = Field(description="Trading exchange")
    contract_id: str | None = Field(description="IB contract ID")
    sec_type: str | None = Field(description="IB security type")
    currency: str = Field(description="Trading currency")
    multiplier: Decimal = Field(description="Contract multiplier")

    # Option-specific fields
    strike_price: Decimal | None = Field(description="Option strike price")
    expiration_date: date | None = Field(description="Option expiration date")
    option_type: str | None = Field(description="Option type (CALL/PUT)")

    # Trading information
    min_tick_size: Decimal = Field(description="Minimum tick size")
    min_order_size: Decimal = Field(description="Minimum order size")
    max_order_size: Decimal | None = Field(description="Maximum order size")

    # Market data
    last_price: Decimal | None = Field(description="Last traded price")
    last_updated: datetime | None = Field(description="Last price update time")
    bid_price: Decimal | None = Field(description="Current bid price")
    ask_price: Decimal | None = Field(description="Current ask price")
    volume: int | None = Field(description="Trading volume")

    # Status
    is_active: bool = Field(description="Whether instrument is active")
    is_tradable: bool = Field(description="Whether instrument can be traded")

    # Metadata
    description: str | None = Field(description="Instrument description")
    sector: str | None = Field(description="Business sector")
    industry: str | None = Field(description="Industry classification")
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class InstrumentFilterSchema(BaseFilterSchema):
    """Instrument filter schema."""

    symbol: str | None = Field(description="Filter by symbol")
    instrument_type: str | None = Field(description="Filter by instrument type")
    exchange: str | None = Field(description="Filter by exchange")
    currency: str | None = Field(description="Filter by currency")
    is_active: bool | None = Field(description="Filter by active status")
    is_tradable: bool | None = Field(description="Filter by tradable status")


# =============================================================================
# ORDER SCHEMAS
# =============================================================================


class OrderCreateSchema(Schema):
    """Order creation schema."""

    instrument_symbol: str = Field(description="Trading symbol")
    broker_account_id: str = Field(description="Broker account ID")
    order_type: str = Field(description="Order type (MARKET, LIMIT, etc.)")
    side: str = Field(description="Order side (BUY, SELL, etc.)")
    quantity: Decimal = Field(description="Order quantity")
    price: Decimal | None = Field(description="Limit price (required for LIMIT orders)")
    stop_price: Decimal | None = Field(description="Stop price (for STOP orders)")
    trailing_percent: Decimal | None = Field(description="Trailing stop percentage")
    time_in_force: str = Field(description="Time in force", default="DAY")
    notes: str | None = Field(description="Order notes")
    metadata: dict[str, Any] | None = Field(description="Additional metadata")

    @validator("price")
    @classmethod
    def validate_price(cls, v, values):
        """Validate price is provided for LIMIT orders."""
        if values.get("order_type") in ["LIMIT", "STOP_LIMIT"] and v is None:
            raise ValueError("Price is required for LIMIT orders")
        return v

    @validator("stop_price")
    @classmethod
    def validate_stop_price(cls, v, values):
        """Validate stop price is provided for STOP orders."""
        if values.get("order_type") in ["STOP", "STOP_LIMIT"] and v is None:
            raise ValueError("Stop price is required for STOP orders")
        return v


class OrderUpdateSchema(Schema):
    """Order update schema."""

    price: Decimal | None = Field(description="New limit price")
    stop_price: Decimal | None = Field(description="New stop price")
    quantity: Decimal | None = Field(description="New quantity")
    time_in_force: str | None = Field(description="New time in force")
    notes: str | None = Field(description="Order notes")
    metadata: dict[str, Any] | None = Field(description="Additional metadata")


class OrderResponseSchema(Schema):
    """Order response schema."""

    id: str = Field(description="Order ID")
    tenant_id: str = Field(description="Tenant ID")
    user_id: str = Field(description="User ID")
    broker_account_id: str = Field(description="Broker account ID")
    instrument_id: str = Field(description="Instrument ID")
    strategy_run_id: str | None = Field(description="Strategy run ID")

    # Order details
    client_order_id: str = Field(description="Client order ID")
    broker_order_id: str | None = Field(description="Broker order ID")

    order_type: str = Field(description="Order type")
    side: str = Field(description="Order side")
    quantity: Decimal = Field(description="Order quantity")

    # Pricing
    price: Decimal | None = Field(description="Limit price")
    stop_price: Decimal | None = Field(description="Stop price")
    trailing_percent: Decimal | None = Field(description="Trailing stop percentage")

    # Time and state
    time_in_force: str = Field(description="Time in force")
    state: str = Field(description="Order state")

    # Strategy information
    strategy_run_id: str | None = Field(description="Strategy run ID")

    # Timestamps
    submitted_at: datetime | None = Field(description="Submission timestamp")
    filled_at: datetime | None = Field(description="Fill timestamp")
    cancelled_at: datetime | None = Field(description="Cancellation timestamp")

    # Execution information
    filled_quantity: Decimal = Field(description="Filled quantity")
    average_price: Decimal | None = Field(description="Average fill price")
    commission: Decimal = Field(description="Total commission")

    # Rejection information
    reject_reason: str | None = Field(description="Rejection reason")
    reject_code: str | None = Field(description="Rejection code")

    # Risk and compliance
    risk_check_passed: bool | None = Field(description="Risk check result")
    compliance_check_passed: bool | None = Field(description="Compliance check result")

    # Metadata
    notes: str | None = Field(description="Order notes")
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    # Computed fields
    remaining_quantity: Decimal = Field(description="Remaining quantity")
    total_value: Decimal | None = Field(description="Total order value")


class OrderFilterSchema(StatusFilterSchema, DateRangeFilterSchema):
    """Order filter schema."""

    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    broker_account_id: str | None = Field(description="Filter by broker account")
    order_type: str | None = Field(description="Filter by order type")
    side: str | None = Field(description="Filter by order side")
    strategy_run_id: str | None = Field(description="Filter by strategy run")
    user_id: str | None = Field(description="Filter by user")


class BulkOrderCreateSchema(Schema):
    """Bulk order creation schema."""

    orders: list[OrderCreateSchema] = Field(description="List of orders to create")
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkOrderResponseSchema(Schema):
    """Bulk order response schema."""

    accepted: list[OrderResponseSchema] = Field(
        description="Successfully created orders"
    )
    rejected: list[dict[str, Any]] = Field(
        description="Failed orders with error details"
    )


# =============================================================================
# EXECUTION SCHEMAS
# =============================================================================


class ExecutionResponseSchema(Schema):
    """Execution response schema."""

    id: str = Field(description="Execution ID")
    tenant_id: str = Field(description="Tenant ID")
    order_id: str = Field(description="Order ID")

    # Execution details
    execution_id: str = Field(description="Execution ID")
    broker_execution_id: str | None = Field(description="Broker execution ID")

    quantity: Decimal = Field(description="Executed quantity")
    price: Decimal = Field(description="Execution price")
    commission: Decimal = Field(description="Commission")
    currency: str = Field(description="Currency")

    # Timestamps
    executed_at: datetime = Field(description="Execution timestamp")

    # Market information
    exchange: str | None = Field(description="Execution exchange")
    liquidity: str | None = Field(description="Liquidity provider")

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ExecutionFilterSchema(DateRangeFilterSchema):
    """Execution filter schema."""

    order_id: str | None = Field(description="Filter by order ID")
    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    broker_account_id: str | None = Field(description="Filter by broker account")


# =============================================================================
# POSITION SCHEMAS
# =============================================================================


class PositionResponseSchema(Schema):
    """Position response schema."""

    id: str = Field(description="Position ID")
    tenant_id: str = Field(description="Tenant ID")
    broker_account_id: str = Field(description="Broker account ID")
    instrument_id: str = Field(description="Instrument ID")

    # Position details
    quantity: Decimal = Field(description="Position quantity")
    average_cost: Decimal | None = Field(description="Average cost basis")

    # Market value
    market_price: Decimal | None = Field(description="Current market price")
    market_value: Decimal | None = Field(description="Current market value")

    # P&L
    unrealized_pnl: Decimal = Field(description="Unrealized P&L")
    realized_pnl: Decimal = Field(description="Realized P&L")

    # Timestamps
    last_updated: datetime = Field(description="Last update timestamp")

    # Metadata
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Computed fields
    is_long: bool = Field(description="Whether position is long")
    is_short: bool = Field(description="Whether position is short")
    is_flat: bool = Field(description="Whether position is flat")


class PositionFilterSchema(BaseFilterSchema):
    """Position filter schema."""

    instrument_symbol: str | None = Field(description="Filter by instrument symbol")
    broker_account_id: str | None = Field(description="Filter by broker account")
    has_position: bool | None = Field(description="Filter by whether position exists")


# =============================================================================
# P&L SNAPSHOT SCHEMAS
# =============================================================================


class PnLSnapshotResponseSchema(Schema):
    """P&L snapshot response schema."""

    id: str = Field(description="Snapshot ID")
    tenant_id: str = Field(description="Tenant ID")
    broker_account_id: str = Field(description="Broker account ID")

    # Snapshot details
    snapshot_date: date = Field(description="Snapshot date")

    # P&L summary
    total_unrealized_pnl: Decimal = Field(description="Total unrealized P&L")
    total_realized_pnl: Decimal = Field(description="Total realized P&L")
    total_commission: Decimal = Field(description="Total commission")

    # Position summary
    total_positions: int = Field(description="Total number of positions")
    long_positions: int = Field(description="Number of long positions")
    short_positions: int = Field(description="Number of short positions")

    # Market data
    total_market_value: Decimal = Field(description="Total market value")
    total_cost_basis: Decimal = Field(description="Total cost basis")

    # Metadata
    positions_snapshot: dict[str, Any] = Field(description="Positions snapshot")
    metadata: dict[str, Any] = Field(description="Additional metadata")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    # Computed fields
    net_pnl: Decimal = Field(description="Net P&L (realized + unrealized)")


class PnLFilterSchema(DateRangeFilterSchema):
    """P&L filter schema."""

    broker_account_id: str | None = Field(description="Filter by broker account")


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================


class BulkCancelSchema(Schema):
    """Bulk cancel schema."""

    order_ids: list[str] = Field(description="List of order IDs to cancel")
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkCancelResponseSchema(Schema):
    """Bulk cancel response schema."""

    accepted: list[str] = Field(description="Successfully cancelled order IDs")
    rejected: list[dict[str, Any]] = Field(
        description="Failed cancellations with error details"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class OrderListResponseSchema(Schema):
    """Order list response schema."""

    orders: list[OrderResponseSchema] = Field(description="List of orders")
    total_count: int = Field(description="Total number of orders")
    has_next: bool = Field(description="Whether there are more orders")


class ExecutionListResponseSchema(Schema):
    """Execution list response schema."""

    executions: list[ExecutionResponseSchema] = Field(description="List of executions")
    total_count: int = Field(description="Total number of executions")
    has_next: bool = Field(description="Whether there are more executions")


class PositionListResponseSchema(Schema):
    """Position list response schema."""

    positions: list[PositionResponseSchema] = Field(description="List of positions")
    total_count: int = Field(description="Total number of positions")
    has_next: bool = Field(description="Whether there are more positions")


class PnLListResponseSchema(Schema):
    """P&L list response schema."""

    snapshots: list[PnLSnapshotResponseSchema] = Field(
        description="List of P&L snapshots"
    )
    total_count: int = Field(description="Total number of snapshots")
    has_next: bool = Field(description="Whether there are more snapshots")
