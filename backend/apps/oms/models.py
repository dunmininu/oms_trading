"""
OMS models for order management, positions, and executions.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel, TenantAwareModel


class Instrument(BaseModel):
    """Financial instrument model."""
    
    INSTRUMENT_TYPE_CHOICES = [
        ('STOCK', 'Stock'),
        ('OPTION', 'Option'),
        ('FUTURE', 'Future'),
        ('FOREX', 'Forex'),
        ('BOND', 'Bond'),
        ('ETF', 'ETF'),
        ('MUTUAL_FUND', 'Mutual Fund'),
        ('CRYPTO', 'Cryptocurrency'),
        ('OTHER', 'Other'),
    ]
    
    EXCHANGE_CHOICES = [
        ('NYSE', 'New York Stock Exchange'),
        ('NASDAQ', 'NASDAQ'),
        ('ARCA', 'NYSE Arca'),
        ('BATS', 'BATS Exchange'),
        ('EDGX', 'EDGX Exchange'),
        ('EDGA', 'EDGA Exchange'),
        ('IB_SMART', 'IB Smart Routing'),
        ('IB_CRYPTO', 'IB Crypto'),
        ('IB_FOREX', 'IB Forex'),
        ('IB_FUTURES', 'IB Futures'),
        ('CBOE', 'CBOE Options Exchange'),
        ('CME', 'CME Group'),
        ('ICE', 'Intercontinental Exchange'),
        ('LSE', 'London Stock Exchange'),
        ('TSE', 'Tokyo Stock Exchange'),
        ('OTHER', 'Other Exchange'),
    ]
    
    # Basic Information
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    instrument_type = models.CharField(max_length=20, choices=INSTRUMENT_TYPE_CHOICES, db_index=True)
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES, db_index=True)
    
    # Contract Details
    contract_id = models.CharField(max_length=100, blank=True)  # IB contract ID
    sec_type = models.CharField(max_length=20, blank=True)  # IB security type
    currency = models.CharField(max_length=3, default='USD')
    multiplier = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('1.0000'))
    
    # Option-specific fields
    strike_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    option_type = models.CharField(
        max_length=4,
        choices=[('CALL', 'Call'), ('PUT', 'Put')],
        blank=True
    )
    
    # Trading Information
    min_tick_size = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.01'))
    min_order_size = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('1.0000'))
    max_order_size = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    
    # Market Data
    last_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    bid_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    ask_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_tradable = models.BooleanField(default=True, db_index=True)
    
    # Metadata
    description = models.TextField(blank=True)
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'oms_instrument'
        verbose_name = _('instrument')
        verbose_name_plural = _('instruments')
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['instrument_type']),
            models.Index(fields=['exchange']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_tradable']),
            models.Index(fields=['expiration_date']),
        ]
    
    def __str__(self):
        return f"{self.symbol} ({self.name})"
    
    def clean(self):
        """Validate instrument data."""
        if self.instrument_type == 'OPTION':
            if not self.strike_price:
                raise ValidationError("Strike price is required for options")
            if not self.expiration_date:
                raise ValidationError("Expiration date is required for options")
            if not self.option_type:
                raise ValidationError("Option type is required for options")


class Order(BaseModel):
    """Order model for managing trading orders."""
    
    ORDER_TYPE_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('STOP', 'Stop'),
        ('STOP_LIMIT', 'Stop Limit'),
        ('TRAILING_STOP', 'Trailing Stop'),
        ('TRAILING_STOP_LIMIT', 'Trailing Stop Limit'),
        ('PEGGED', 'Pegged'),
        ('AUCTION', 'Auction'),
        ('VOLATILITY', 'Volatility'),
        ('ADAPTIVE', 'Adaptive'),
    ]
    
    SIDE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('BUY_TO_COVER', 'Buy to Cover'),
        ('SELL_SHORT', 'Sell Short'),
    ]
    
    TIME_IN_FORCE_CHOICES = [
        ('DAY', 'Day'),
        ('GTC', 'Good Till Cancelled'),
        ('IOC', 'Immediate or Cancel'),
        ('FOK', 'Fill or Kill'),
        ('GTD', 'Good Till Date'),
        ('OPG', 'Opening'),
        ('CLS', 'Closing'),
        ('MOC', 'Market on Close'),
        ('LOC', 'Limit on Close'),
    ]
    
    STATE_CHOICES = [
        ('NEW', 'New'),
        ('PENDING_SUBMIT', 'Pending Submit'),
        ('SUBMITTED', 'Submitted'),
        ('PENDING_CANCEL', 'Pending Cancel'),
        ('CANCELLED', 'Cancelled'),
        ('FILLED', 'Filled'),
        ('PARTIALLY_FILLED', 'Partially Filled'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
        ('PENDING_REPLACE', 'Pending Replace'),
        ('REPLACED', 'Replaced'),
        ('ROUTED', 'Routed'),
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('RISK_REJECTED', 'Risk Rejected'),
        ('COMPLIANCE_REJECTED', 'Compliance Rejected'),
    ]
    
    # Core Order Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True
    )
    broker_account = models.ForeignKey(
        'brokers.BrokerAccount',
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True
    )
    
    # Order Details
    client_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    broker_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, db_index=True)
    side = models.CharField(max_length=20, choices=SIDE_CHOICES, db_index=True)
    quantity = models.DecimalField(
        max_digits=15, decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    
    # Pricing
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    trailing_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Time and State
    time_in_force = models.CharField(max_length=20, choices=TIME_IN_FORCE_CHOICES, default='DAY')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='NEW', db_index=True)
    
    # Strategy Information
    strategy_run = models.ForeignKey(
        'strategies.StrategyRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Execution Information
    filled_quantity = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    average_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Rejection Information
    reject_reason = models.TextField(blank=True)
    reject_code = models.CharField(max_length=50, blank=True)
    
    # Risk and Compliance
    risk_check_passed = models.BooleanField(null=True, blank=True)
    compliance_check_passed = models.BooleanField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'oms_order'
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        indexes = [
            models.Index(fields=['client_order_id']),
            models.Index(fields=['broker_order_id']),
            models.Index(fields=['state']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['user', 'submitted_at']),
            models.Index(fields=['broker_account', 'submitted_at']),
            models.Index(fields=['instrument', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.client_order_id} - {self.side} {self.quantity} {self.instrument.symbol}"
    
    @property
    def is_active(self):
        """Check if order is in an active state."""
        return self.state in ['NEW', 'PENDING_SUBMIT', 'SUBMITTED', 'PENDING_CANCEL', 'PENDING_REPLACE']
    
    @property
    def is_filled(self):
        """Check if order is completely filled."""
        return self.state == 'FILLED'
    
    @property
    def is_partially_filled(self):
        """Check if order is partially filled."""
        return self.state == 'PARTIALLY_FILLED'
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to be filled."""
        return self.quantity - self.filled_quantity
    
    @property
    def total_value(self):
        """Calculate total order value."""
        if self.price:
            return self.quantity * self.price
        return None
    
    def clean(self):
        """Validate order data."""
        if self.order_type in ['LIMIT', 'STOP_LIMIT'] and not self.price:
            raise ValidationError("Price is required for limit orders")
        
        if self.order_type in ['STOP', 'STOP_LIMIT'] and not self.stop_price:
            raise ValidationError("Stop price is required for stop orders")
        
        if self.order_type == 'TRAILING_STOP' and not self.trailing_percent:
            raise ValidationError("Trailing percent is required for trailing stop orders")


class Execution(BaseModel):
    """Execution model for tracking order fills."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='executions',
        db_index=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='executions',
        db_index=True
    )
    
    # Execution Details
    execution_id = models.CharField(max_length=100, unique=True, db_index=True)
    broker_execution_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    price = models.DecimalField(max_digits=15, decimal_places=4)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    
    # Timestamps
    executed_at = models.DateTimeField()
    
    # Market Information
    exchange = models.CharField(max_length=20, blank=True)
    liquidity = models.CharField(max_length=20, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'oms_execution'
        verbose_name = _('execution')
        verbose_name_plural = _('executions')
        indexes = [
            models.Index(fields=['execution_id']),
            models.Index(fields=['broker_execution_id']),
            models.Index(fields=['executed_at']),
            models.Index(fields=['order', 'executed_at']),
        ]
    
    def __str__(self):
        return f"{self.execution_id} - {self.quantity} @ {self.price}"


class Position(BaseModel):
    """Position model for tracking current holdings."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='positions',
        db_index=True
    )
    broker_account = models.ForeignKey(
        'brokers.BrokerAccount',
        on_delete=models.CASCADE,
        related_name='positions',
        db_index=True
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='positions',
        db_index=True
    )
    
    # Position Details
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.0000'))
    average_cost = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    
    # Market Value
    market_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    market_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # P&L
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'oms_position'
        verbose_name = _('position')
        verbose_name_plural = _('positions')
        unique_together = ['tenant', 'broker_account', 'instrument']
        indexes = [
            models.Index(fields=['tenant', 'instrument']),
            models.Index(fields=['broker_account', 'instrument']),
            models.Index(fields=['quantity']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol}: {self.quantity} @ {self.average_cost or 'N/A'}"
    
    @property
    def is_long(self):
        """Check if position is long."""
        return self.quantity > 0
    
    @property
    def is_short(self):
        """Check if position is short."""
        return self.quantity < 0
    
    @property
    def is_flat(self):
        """Check if position is flat."""
        return self.quantity == 0
    
    def update_market_value(self, market_price):
        """Update market value and unrealized P&L."""
        self.market_price = market_price
        if self.quantity != 0 and self.average_cost:
            self.market_value = abs(self.quantity) * market_price
            if self.is_long:
                self.unrealized_pnl = (market_price - self.average_cost) * self.quantity
            else:
                self.unrealized_pnl = (self.average_cost - market_price) * abs(self.quantity)
        else:
            self.market_value = Decimal('0.00')
            self.unrealized_pnl = Decimal('0.00')


class PnLSnapshot(BaseModel):
    """Daily P&L snapshot for reporting and analysis."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='pnl_snapshots',
        db_index=True
    )
    broker_account = models.ForeignKey(
        'brokers.BrokerAccount',
        on_delete=models.CASCADE,
        related_name='pnl_snapshots',
        db_index=True
    )
    
    # Snapshot Details
    snapshot_date = models.DateField(db_index=True)
    
    # P&L Summary
    total_unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Position Summary
    total_positions = models.PositiveIntegerField(default=0)
    long_positions = models.PositiveIntegerField(default=0)
    short_positions = models.PositiveIntegerField(default=0)
    
    # Market Data
    total_market_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cost_basis = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    positions_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'oms_pnl_snapshot'
        verbose_name = _('P&L snapshot')
        verbose_name_plural = _('P&L snapshots')
        unique_together = ['tenant', 'broker_account', 'snapshot_date']
        indexes = [
            models.Index(fields=['snapshot_date']),
            models.Index(fields=['tenant', 'snapshot_date']),
            models.Index(fields=['broker_account', 'snapshot_date']),
        ]
    
    def __str__(self):
        return f"P&L Snapshot for {self.broker_account.account_name} on {self.snapshot_date}"
    
    @property
    def net_pnl(self):
        """Calculate net P&L."""
        return self.total_unrealized_pnl + self.total_realized_pnl - self.total_commission
