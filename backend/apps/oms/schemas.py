"""
OMS schemas for Django Ninja API.
"""

from ninja import Schema, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
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
    contract_id: Optional[str] = Field(description="IB contract ID")
    sec_type: Optional[str] = Field(description="IB security type")
    currency: str = Field(description="Trading currency")
    multiplier: Decimal = Field(description="Contract multiplier")
    
    # Option-specific fields
    strike_price: Optional[Decimal] = Field(description="Option strike price")
    expiration_date: Optional[date] = Field(description="Option expiration date")
    option_type: Optional[str] = Field(description="Option type (CALL/PUT)")
    
    # Trading information
    min_tick_size: Decimal = Field(description="Minimum tick size")
    min_order_size: Decimal = Field(description="Minimum order size")
    max_order_size: Optional[Decimal] = Field(description="Maximum order size")
    
    # Market data
    last_price: Optional[Decimal] = Field(description="Last traded price")
    last_updated: Optional[datetime] = Field(description="Last price update time")
    bid_price: Optional[Decimal] = Field(description="Current bid price")
    ask_price: Optional[Decimal] = Field(description="Current ask price")
    volume: Optional[int] = Field(description="Trading volume")
    
    # Status
    is_active: bool = Field(description="Whether instrument is active")
    is_tradable: bool = Field(description="Whether instrument can be traded")
    
    # Metadata
    description: Optional[str] = Field(description="Instrument description")
    sector: Optional[str] = Field(description="Business sector")
    industry: Optional[str] = Field(description="Industry classification")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class InstrumentFilterSchema(BaseFilterSchema):
    """Instrument filter schema."""
    
    symbol: Optional[str] = Field(description="Filter by symbol")
    instrument_type: Optional[str] = Field(description="Filter by instrument type")
    exchange: Optional[str] = Field(description="Filter by exchange")
    currency: Optional[str] = Field(description="Filter by currency")
    is_active: Optional[bool] = Field(description="Filter by active status")
    is_tradable: Optional[bool] = Field(description="Filter by tradable status")


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
    price: Optional[Decimal] = Field(description="Limit price (required for LIMIT orders)")
    stop_price: Optional[Decimal] = Field(description="Stop price (for STOP orders)")
    trailing_percent: Optional[Decimal] = Field(description="Trailing stop percentage")
    time_in_force: str = Field(description="Time in force", default="DAY")
    notes: Optional[str] = Field(description="Order notes")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")
    
    @validator('price')
    def validate_price(cls, v, values):
        """Validate price is provided for LIMIT orders."""
        if values.get('order_type') in ['LIMIT', 'STOP_LIMIT'] and v is None:
            raise ValueError('Price is required for LIMIT orders')
        return v
    
    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        """Validate stop price is provided for STOP orders."""
        if values.get('order_type') in ['STOP', 'STOP_LIMIT'] and v is None:
            raise ValueError('Stop price is required for STOP orders')
        return v


class OrderUpdateSchema(Schema):
    """Order update schema."""
    
    price: Optional[Decimal] = Field(description="New limit price")
    stop_price: Optional[Decimal] = Field(description="New stop price")
    quantity: Optional[Decimal] = Field(description="New quantity")
    time_in_force: Optional[str] = Field(description="New time in force")
    notes: Optional[str] = Field(description="Order notes")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")


class OrderResponseSchema(Schema):
    """Order response schema."""
    
    id: str = Field(description="Order ID")
    tenant_id: str = Field(description="Tenant ID")
    user_id: str = Field(description="User ID")
    broker_account_id: str = Field(description="Broker account ID")
    instrument_id: str = Field(description="Instrument ID")
    strategy_run_id: Optional[str] = Field(description="Strategy run ID")
    
    # Order details
    client_order_id: str = Field(description="Client order ID")
    broker_order_id: Optional[str] = Field(description="Broker order ID")
    
    order_type: str = Field(description="Order type")
    side: str = Field(description="Order side")
    quantity: Decimal = Field(description="Order quantity")
    
    # Pricing
    price: Optional[Decimal] = Field(description="Limit price")
    stop_price: Optional[Decimal] = Field(description="Stop price")
    trailing_percent: Optional[Decimal] = Field(description="Trailing stop percentage")
    
    # Time and state
    time_in_force: str = Field(description="Time in force")
    state: str = Field(description="Order state")
    
    # Strategy information
    strategy_run_id: Optional[str] = Field(description="Strategy run ID")
    
    # Timestamps
    submitted_at: Optional[datetime] = Field(description="Submission timestamp")
    filled_at: Optional[datetime] = Field(description="Fill timestamp")
    cancelled_at: Optional[datetime] = Field(description="Cancellation timestamp")
    
    # Execution information
    filled_quantity: Decimal = Field(description="Filled quantity")
    average_price: Optional[Decimal] = Field(description="Average fill price")
    commission: Decimal = Field(description="Total commission")
    
    # Rejection information
    reject_reason: Optional[str] = Field(description="Rejection reason")
    reject_code: Optional[str] = Field(description="Rejection code")
    
    # Risk and compliance
    risk_check_passed: Optional[bool] = Field(description="Risk check result")
    compliance_check_passed: Optional[bool] = Field(description="Compliance check result")
    
    # Metadata
    notes: Optional[str] = Field(description="Order notes")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Computed fields
    remaining_quantity: Decimal = Field(description="Remaining quantity")
    total_value: Optional[Decimal] = Field(description="Total order value")


class OrderFilterSchema(StatusFilterSchema, DateRangeFilterSchema):
    """Order filter schema."""
    
    instrument_symbol: Optional[str] = Field(description="Filter by instrument symbol")
    broker_account_id: Optional[str] = Field(description="Filter by broker account")
    order_type: Optional[str] = Field(description="Filter by order type")
    side: Optional[str] = Field(description="Filter by order side")
    strategy_run_id: Optional[str] = Field(description="Filter by strategy run")
    user_id: Optional[str] = Field(description="Filter by user")


class BulkOrderCreateSchema(Schema):
    """Bulk order creation schema."""
    
    orders: List[OrderCreateSchema] = Field(description="List of orders to create")
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkOrderResponseSchema(Schema):
    """Bulk order response schema."""
    
    accepted: List[OrderResponseSchema] = Field(description="Successfully created orders")
    rejected: List[Dict[str, Any]] = Field(description="Failed orders with error details")


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
    broker_execution_id: Optional[str] = Field(description="Broker execution ID")
    
    quantity: Decimal = Field(description="Executed quantity")
    price: Decimal = Field(description="Execution price")
    commission: Decimal = Field(description="Commission")
    currency: str = Field(description="Currency")
    
    # Timestamps
    executed_at: datetime = Field(description="Execution timestamp")
    
    # Market information
    exchange: Optional[str] = Field(description="Execution exchange")
    liquidity: Optional[str] = Field(description="Liquidity provider")
    
    # Metadata
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ExecutionFilterSchema(DateRangeFilterSchema):
    """Execution filter schema."""
    
    order_id: Optional[str] = Field(description="Filter by order ID")
    instrument_symbol: Optional[str] = Field(description="Filter by instrument symbol")
    broker_account_id: Optional[str] = Field(description="Filter by broker account")


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
    average_cost: Optional[Decimal] = Field(description="Average cost basis")
    
    # Market value
    market_price: Optional[Decimal] = Field(description="Current market price")
    market_value: Optional[Decimal] = Field(description="Current market value")
    
    # P&L
    unrealized_pnl: Decimal = Field(description="Unrealized P&L")
    realized_pnl: Decimal = Field(description="Realized P&L")
    
    # Timestamps
    last_updated: datetime = Field(description="Last update timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Computed fields
    is_long: bool = Field(description="Whether position is long")
    is_short: bool = Field(description="Whether position is short")
    is_flat: bool = Field(description="Whether position is flat")


class PositionFilterSchema(BaseFilterSchema):
    """Position filter schema."""
    
    instrument_symbol: Optional[str] = Field(description="Filter by instrument symbol")
    broker_account_id: Optional[str] = Field(description="Filter by broker account")
    has_position: Optional[bool] = Field(description="Filter by whether position exists")


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
    positions_snapshot: Dict[str, Any] = Field(description="Positions snapshot")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Computed fields
    net_pnl: Decimal = Field(description="Net P&L (realized + unrealized)")


class PnLFilterSchema(DateRangeFilterSchema):
    """P&L filter schema."""
    
    broker_account_id: Optional[str] = Field(description="Filter by broker account")


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================

class BulkCancelSchema(Schema):
    """Bulk cancel schema."""
    
    order_ids: List[str] = Field(description="List of order IDs to cancel")
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkCancelResponseSchema(Schema):
    """Bulk cancel response schema."""
    
    accepted: List[str] = Field(description="Successfully cancelled order IDs")
    rejected: List[Dict[str, Any]] = Field(description="Failed cancellations with error details")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class OrderListResponseSchema(Schema):
    """Order list response schema."""
    
    orders: List[OrderResponseSchema] = Field(description="List of orders")
    total_count: int = Field(description="Total number of orders")
    has_next: bool = Field(description="Whether there are more orders")


class ExecutionListResponseSchema(Schema):
    """Execution list response schema."""
    
    executions: List[ExecutionResponseSchema] = Field(description="List of executions")
    total_count: int = Field(description="Total number of executions")
    has_next: bool = Field(description="Whether there are more executions")


class PositionListResponseSchema(Schema):
    """Position list response schema."""
    
    positions: List[PositionResponseSchema] = Field(description="List of positions")
    total_count: int = Field(description="Total number of positions")
    has_next: bool = Field(description="Whether there are more positions")


class PnLListResponseSchema(Schema):
    """P&L list response schema."""
    
    snapshots: List[PnLSnapshotResponseSchema] = Field(description="List of P&L snapshots")
    total_count: int = Field(description="Total number of snapshots")
    has_next: bool = Field(description="Whether there are more snapshots")
