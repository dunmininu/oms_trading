"""
Strategy schemas for Django Ninja API.
"""

from ninja import Schema, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from pydantic import validator

from apps.api.schemas import BaseFilterSchema, DateRangeFilterSchema, StatusFilterSchema


# =============================================================================
# STRATEGY DEFINITION SCHEMAS
# =============================================================================

class StrategyDefinitionCreateSchema(Schema):
    """Strategy definition creation schema."""
    
    name: str = Field(description="Strategy name")
    description: Optional[str] = Field(description="Strategy description")
    version: str = Field(description="Strategy version")
    
    # Strategy configuration
    strategy_type: str = Field(description="Strategy type (ALPHA, ARBITRAGE, etc.)")
    risk_profile: str = Field(description="Risk profile (CONSERVATIVE, MODERATE, AGGRESSIVE)")
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Trading parameters
    instruments: List[str] = Field(description="List of instrument symbols")
    trading_hours: Dict[str, Any] = Field(description="Trading hours configuration")
    rebalance_frequency: str = Field(description="Rebalance frequency (DAILY, WEEKLY, etc.)")
    
    # Risk management
    stop_loss: Optional[Decimal] = Field(description="Stop loss percentage")
    take_profit: Optional[Decimal] = Field(description="Take profit percentage")
    max_slippage: Optional[Decimal] = Field(description="Maximum slippage tolerance")
    
    # Metadata
    tags: Optional[List[str]] = Field(description="Strategy tags")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")


class StrategyDefinitionUpdateSchema(Schema):
    """Strategy definition update schema."""
    
    name: Optional[str] = Field(description="Strategy name")
    description: Optional[str] = Field(description="Strategy description")
    version: Optional[str] = Field(description="Strategy version")
    
    # Strategy configuration
    strategy_type: Optional[str] = Field(description="Strategy type")
    risk_profile: Optional[str] = Field(description="Risk profile")
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Trading parameters
    instruments: Optional[List[str]] = Field(description="List of instrument symbols")
    trading_hours: Optional[Dict[str, Any]] = Field(description="Trading hours configuration")
    rebalance_frequency: Optional[str] = Field(description="Rebalance frequency")
    
    # Risk management
    stop_loss: Optional[Decimal] = Field(description="Stop loss percentage")
    take_profit: Optional[Decimal] = Field(description="Take profit percentage")
    max_slippage: Optional[Decimal] = Field(description="Maximum slippage tolerance")
    
    # Status
    is_active: Optional[bool] = Field(description="Whether strategy is active")
    
    # Metadata
    tags: Optional[List[str]] = Field(description="Strategy tags")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")


class StrategyDefinitionResponseSchema(Schema):
    """Strategy definition response schema."""
    
    id: str = Field(description="Strategy definition ID")
    tenant_id: str = Field(description="Tenant ID")
    user_id: str = Field(description="User ID")
    
    # Strategy details
    name: str = Field(description="Strategy name")
    description: Optional[str] = Field(description="Strategy description")
    version: str = Field(description="Strategy version")
    
    # Strategy configuration
    strategy_type: str = Field(description="Strategy type")
    risk_profile: str = Field(description="Risk profile")
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Trading parameters
    instruments: List[str] = Field(description="List of instrument symbols")
    trading_hours: Dict[str, Any] = Field(description="Trading hours configuration")
    rebalance_frequency: str = Field(description="Rebalance frequency")
    
    # Risk management
    stop_loss: Optional[Decimal] = Field(description="Stop loss percentage")
    take_profit: Optional[Decimal] = Field(description="Take profit percentage")
    max_slippage: Optional[Decimal] = Field(description="Maximum slippage tolerance")
    
    # Status
    is_active: bool = Field(description="Whether strategy is active")
    is_approved: bool = Field(description="Whether strategy is approved")
    
    # Performance metrics
    total_runs: int = Field(description="Total number of strategy runs")
    successful_runs: int = Field(description="Number of successful runs")
    total_pnl: Decimal = Field(description="Total P&L across all runs")
    sharpe_ratio: Optional[Decimal] = Field(description="Sharpe ratio")
    max_drawdown_actual: Optional[Decimal] = Field(description="Actual maximum drawdown")
    
    # Metadata
    tags: List[str] = Field(description="Strategy tags")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    approved_at: Optional[datetime] = Field(description="Approval timestamp")


class StrategyDefinitionFilterSchema(StatusFilterSchema):
    """Strategy definition filter schema."""
    
    name: Optional[str] = Field(description="Filter by strategy name")
    strategy_type: Optional[str] = Field(description="Filter by strategy type")
    risk_profile: Optional[str] = Field(description="Filter by risk profile")
    user_id: Optional[str] = Field(description="Filter by user")
    is_approved: Optional[bool] = Field(description="Filter by approval status")
    tags: Optional[List[str]] = Field(description="Filter by tags")


# =============================================================================
# STRATEGY RUN SCHEMAS
# =============================================================================

class StrategyRunCreateSchema(Schema):
    """Strategy run creation schema."""
    
    strategy_definition_id: str = Field(description="Strategy definition ID")
    broker_account_id: str = Field(description="Broker account ID")
    
    # Run configuration
    initial_capital: Decimal = Field(description="Initial capital for the run")
    max_positions: Optional[int] = Field(description="Maximum number of positions")
    
    # Risk parameters
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Schedule
    start_date: date = Field(description="Run start date")
    end_date: Optional[date] = Field(description="Run end date (optional for ongoing runs)")
    
    # Metadata
    notes: Optional[str] = Field(description="Run notes")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")


class StrategyRunUpdateSchema(Schema):
    """Strategy run update schema."""
    
    end_date: Optional[date] = Field(description="Run end date")
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Status
    is_active: Optional[bool] = Field(description="Whether run is active")
    
    # Metadata
    notes: Optional[str] = Field(description="Run notes")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")


class StrategyRunResponseSchema(Schema):
    """Strategy run response schema."""
    
    id: str = Field(description="Strategy run ID")
    tenant_id: str = Field(description="Tenant ID")
    user_id: str = Field(description="User ID")
    strategy_definition_id: str = Field(description="Strategy definition ID")
    broker_account_id: str = Field(description="Broker account ID")
    
    # Run details
    run_name: str = Field(description="Run name")
    run_number: int = Field(description="Run number")
    
    # Configuration
    initial_capital: Decimal = Field(description="Initial capital")
    max_positions: Optional[int] = Field(description="Maximum positions")
    max_position_size: Optional[Decimal] = Field(description="Maximum position size")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown percentage")
    
    # Schedule
    start_date: date = Field(description="Start date")
    end_date: Optional[date] = Field(description="End date")
    
    # Status
    status: str = Field(description="Run status")
    is_active: bool = Field(description="Whether run is active")
    
    # Performance metrics
    current_capital: Decimal = Field(description="Current capital")
    total_pnl: Decimal = Field(description="Total P&L")
    total_return: Decimal = Field(description="Total return percentage")
    daily_pnl: Optional[Decimal] = Field(description="Daily P&L")
    daily_return: Optional[Decimal] = Field(description="Daily return percentage")
    
    # Risk metrics
    current_drawdown: Decimal = Field(description="Current drawdown")
    max_drawdown_actual: Decimal = Field(description="Actual maximum drawdown")
    sharpe_ratio: Optional[Decimal] = Field(description="Sharpe ratio")
    sortino_ratio: Optional[Decimal] = Field(description="Sortino ratio")
    
    # Trading statistics
    total_trades: int = Field(description="Total number of trades")
    winning_trades: int = Field(description="Number of winning trades")
    losing_trades: int = Field(description="Number of losing trades")
    win_rate: Decimal = Field(description="Win rate percentage")
    
    # Position summary
    current_positions: int = Field(description="Current number of positions")
    total_positions_taken: int = Field(description="Total positions taken")
    
    # Timestamps
    started_at: datetime = Field(description="Start timestamp")
    ended_at: Optional[datetime] = Field(description="End timestamp")
    last_trade_at: Optional[datetime] = Field(description="Last trade timestamp")
    
    # Metadata
    notes: Optional[str] = Field(description="Run notes")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class StrategyRunFilterSchema(StatusFilterSchema, DateRangeFilterSchema):
    """Strategy run filter schema."""
    
    strategy_definition_id: Optional[str] = Field(description="Filter by strategy definition")
    broker_account_id: Optional[str] = Field(description="Filter by broker account")
    user_id: Optional[str] = Field(description="Filter by user")
    min_capital: Optional[Decimal] = Field(description="Minimum initial capital")
    max_capital: Optional[Decimal] = Field(description="Maximum initial capital")


# =============================================================================
# STRATEGY PERFORMANCE SCHEMAS
# =============================================================================

class StrategyPerformanceResponseSchema(Schema):
    """Strategy performance response schema."""
    
    id: str = Field(description="Performance ID")
    tenant_id: str = Field(description="Tenant ID")
    strategy_run_id: str = Field(description="Strategy run ID")
    
    # Performance period
    period_start: date = Field(description="Period start date")
    period_end: date = Field(description="Period end date")
    period_type: str = Field(description="Period type (DAILY, WEEKLY, MONTHLY)")
    
    # Return metrics
    period_return: Decimal = Field(description="Period return percentage")
    cumulative_return: Decimal = Field(description="Cumulative return percentage")
    annualized_return: Optional[Decimal] = Field(description="Annualized return percentage")
    
    # Risk metrics
    period_volatility: Optional[Decimal] = Field(description="Period volatility")
    sharpe_ratio: Optional[Decimal] = Field(description="Sharpe ratio")
    sortino_ratio: Optional[Decimal] = Field(description="Sortino ratio")
    max_drawdown: Optional[Decimal] = Field(description="Maximum drawdown")
    
    # Trading metrics
    total_trades: int = Field(description="Total trades in period")
    winning_trades: int = Field(description="Winning trades in period")
    losing_trades: int = Field(description="Losing trades in period")
    win_rate: Decimal = Field(description="Win rate percentage")
    
    # Capital metrics
    starting_capital: Decimal = Field(description="Starting capital")
    ending_capital: Decimal = Field(description="Ending capital")
    period_pnl: Decimal = Field(description="Period P&L")
    
    # Metadata
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class StrategyPerformanceFilterSchema(DateRangeFilterSchema):
    """Strategy performance filter schema."""
    
    strategy_run_id: Optional[str] = Field(description="Filter by strategy run")
    period_type: Optional[str] = Field(description="Filter by period type")
    min_return: Optional[Decimal] = Field(description="Minimum return filter")
    max_return: Optional[Decimal] = Field(description="Maximum return filter")


# =============================================================================
# STRATEGY SIGNAL SCHEMAS
# =============================================================================

class StrategySignalResponseSchema(Schema):
    """Strategy signal response schema."""
    
    id: str = Field(description="Signal ID")
    tenant_id: str = Field(description="Tenant ID")
    strategy_run_id: str = Field(description="Strategy run ID")
    
    # Signal details
    signal_type: str = Field(description="Signal type (BUY, SELL, HOLD)")
    instrument_symbol: str = Field(description="Instrument symbol")
    confidence: Decimal = Field(description="Signal confidence (0-1)")
    
    # Signal parameters
    target_price: Optional[Decimal] = Field(description="Target price")
    stop_loss: Optional[Decimal] = Field(description="Stop loss price")
    take_profit: Optional[Decimal] = Field(description="Take profit price")
    quantity: Optional[Decimal] = Field(description="Suggested quantity")
    
    # Signal context
    signal_reason: str = Field(description="Reason for the signal")
    market_conditions: Dict[str, Any] = Field(description="Market conditions at signal time")
    
    # Status
    is_executed: bool = Field(description="Whether signal was executed")
    execution_price: Optional[Decimal] = Field(description="Execution price")
    execution_quantity: Optional[Decimal] = Field(description="Execution quantity")
    
    # Timestamps
    signal_time: datetime = Field(description="Signal generation time")
    executed_at: Optional[datetime] = Field(description="Execution timestamp")
    
    # Metadata
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class StrategySignalFilterSchema(DateRangeFilterSchema):
    """Strategy signal filter schema."""
    
    strategy_run_id: Optional[str] = Field(description="Filter by strategy run")
    signal_type: Optional[str] = Field(description="Filter by signal type")
    instrument_symbol: Optional[str] = Field(description="Filter by instrument")
    is_executed: Optional[bool] = Field(description="Filter by execution status")
    min_confidence: Optional[Decimal] = Field(description="Minimum confidence filter")


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================

class BulkStrategyRunCreateSchema(Schema):
    """Bulk strategy run creation schema."""
    
    runs: List[StrategyRunCreateSchema] = Field(description="List of strategy runs to create")
    idempotency_key: str = Field(description="Bulk operation idempotency key")


class BulkStrategyRunResponseSchema(Schema):
    """Bulk strategy run response schema."""
    
    accepted: List[StrategyRunResponseSchema] = Field(description="Successfully created runs")
    rejected: List[Dict[str, Any]] = Field(description="Failed runs with error details")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class StrategyDefinitionListResponseSchema(Schema):
    """Strategy definition list response schema."""
    
    strategies: List[StrategyDefinitionResponseSchema] = Field(description="List of strategies")
    total_count: int = Field(description="Total number of strategies")
    has_next: bool = Field(description="Whether there are more strategies")


class StrategyRunListResponseSchema(Schema):
    """Strategy run list response schema."""
    
    runs: List[StrategyRunResponseSchema] = Field(description="List of strategy runs")
    total_count: int = Field(description="Total number of runs")
    has_next: bool = Field(description="Whether there are more runs")


class StrategyPerformanceListResponseSchema(Schema):
    """Strategy performance list response schema."""
    
    performances: List[StrategyPerformanceResponseSchema] = Field(description="List of performances")
    total_count: int = Field(description="Total number of performances")
    has_next: bool = Field(description="Whether there are more performances")


class StrategySignalListResponseSchema(Schema):
    """Strategy signal list response schema."""
    
    signals: List[StrategySignalResponseSchema] = Field(description="List of signals")
    total_count: int = Field(description="Total number of signals")
    has_next: bool = Field(description="Whether there are more signals")
