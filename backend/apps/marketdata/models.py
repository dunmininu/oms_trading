"""
Market data models for managing subscriptions and data streams.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel, TenantAwareModel


class MarketSubscription(BaseModel):
    """Market data subscription model."""
    
    SUBSCRIPTION_TYPE_CHOICES = [
        ('REALTIME', 'Real-time'),
        ('SNAPSHOT', 'Snapshot'),
        ('HISTORICAL', 'Historical'),
        ('OPTION_CHAIN', 'Option Chain'),
        ('LEVEL_1', 'Level 1'),
        ('LEVEL_2', 'Level 2'),
        ('NEWS', 'News'),
        ('FUNDAMENTALS', 'Fundamentals'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
        ('ERROR', 'Error'),
    ]
    
    # Core Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='market_subscriptions',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='market_subscriptions',
        db_index=True
    )
    instrument = models.ForeignKey(
        'oms.Instrument',
        on_delete=models.CASCADE,
        related_name='market_subscriptions',
        db_index=True
    )
    
    # Subscription Details
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    
    # Data Fields
    fields = models.JSONField(default=list, blank=True)  # List of fields to subscribe to
    
    # Schedule
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Rate Limiting
    max_ticks_per_second = models.PositiveIntegerField(null=True, blank=True)
    max_ticks_per_minute = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    last_data_received = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketdata_market_subscription'
        verbose_name = _('market subscription')
        verbose_name_plural = _('market subscriptions')
        unique_together = ['tenant', 'instrument', 'subscription_type']
        indexes = [
            models.Index(fields=['subscription_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_data_received']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.subscription_type}"


class TickData(BaseModel):
    """Real-time tick data model."""
    
    TICK_TYPE_CHOICES = [
        ('BID', 'Bid'),
        ('ASK', 'Ask'),
        ('TRADE', 'Trade'),
        ('BID_SIZE', 'Bid Size'),
        ('ASK_SIZE', 'Ask Size'),
        ('LAST_SIZE', 'Last Size'),
        ('HIGH', 'High'),
        ('LOW', 'Low'),
        ('OPEN', 'Open'),
        ('CLOSE', 'Close'),
        ('VOLUME', 'Volume'),
        ('OPTION_IMPLIED_VOLATILITY', 'Option Implied Volatility'),
        ('OPTION_VOLUME', 'Option Volume'),
        ('OPTION_OPEN_INTEREST', 'Option Open Interest'),
        ('OPTION_DELTA', 'Option Delta'),
        ('OPTION_GAMMA', 'Option Gamma'),
        ('OPTION_THETA', 'Option Theta'),
        ('OPTION_VEGA', 'Option Vega'),
        ('FUTURE_BASIS', 'Future Basis'),
        ('FUTURE_OPEN_INTEREST', 'Future Open Interest'),
        ('NEWS', 'News'),
        ('FUNDAMENTAL', 'Fundamental'),
    ]
    
    # Core Information
    instrument = models.ForeignKey(
        'oms.Instrument',
        on_delete=models.CASCADE,
        related_name='tick_data',
        db_index=True
    )
    
    # Tick Details
    tick_type = models.CharField(max_length=30, choices=TICK_TYPE_CHOICES, db_index=True)
    price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    size = models.BigIntegerField(null=True, blank=True)
    
    # Timestamps
    tick_time = models.DateTimeField(db_index=True)
    
    # Market Information
    exchange = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Additional Data
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    source = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketdata_tick_data'
        verbose_name = _('tick data')
        verbose_name_plural = _('tick data')
        indexes = [
            models.Index(fields=['tick_type']),
            models.Index(fields=['tick_time']),
            models.Index(fields=['instrument', 'tick_time']),
            models.Index(fields=['instrument', 'tick_type', 'tick_time']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.tick_type} @ {self.tick_time}"


class MarketDataCache(BaseModel):
    """Market data cache for frequently accessed data."""
    
    CACHE_TYPE_CHOICES = [
        ('LAST_PRICE', 'Last Price'),
        ('BID_ASK', 'Bid/Ask'),
        ('OHLC', 'OHLC'),
        ('VOLUME', 'Volume'),
        ('GREEKS', 'Option Greeks'),
        ('IMPLIED_VOLATILITY', 'Implied Volatility'),
    ]
    
    # Core Information
    instrument = models.ForeignKey(
        'oms.Instrument',
        on_delete=models.CASCADE,
        related_name='market_data_cache',
        db_index=True
    )
    
    # Cache Details
    cache_type = models.CharField(max_length=30, choices=CACHE_TYPE_CHOICES, db_index=True)
    cache_key = models.CharField(max_length=200, db_index=True)
    
    # Cached Data
    cached_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketdata_market_data_cache'
        verbose_name = _('market data cache')
        verbose_name_plural = _('market data cache')
        unique_together = ['instrument', 'cache_type', 'cache_key']
        indexes = [
            models.Index(fields=['cache_type']),
            models.Index(fields=['last_updated']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['instrument', 'cache_type']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.cache_type}"


class MarketDataStream(BaseModel):
    """Market data stream configuration."""
    
    STREAM_TYPE_CHOICES = [
        ('WEBSOCKET', 'WebSocket'),
        ('SERVER_SENT_EVENTS', 'Server-Sent Events'),
        ('POLLING', 'Polling'),
        ('GRPC', 'gRPC'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('STOPPED', 'Stopped'),
        ('ERROR', 'Error'),
    ]
    
    # Core Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='market_data_streams',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='market_data_streams',
        db_index=True
    )
    
    # Stream Details
    name = models.CharField(max_length=200, db_index=True)
    stream_type = models.CharField(max_length=20, choices=STREAM_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    
    # Subscriptions
    subscriptions = models.ManyToManyField(
        MarketSubscription,
        related_name='data_streams',
        blank=True
    )
    
    # Connection Information
    connection_id = models.CharField(max_length=100, blank=True, db_index=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    last_data_sent = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketdata_market_data_stream'
        verbose_name = _('market data stream')
        verbose_name_plural = _('market data streams')
        unique_together = ['tenant', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['stream_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['connection_id']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.stream_type})"


class HistoricalData(BaseModel):
    """Historical market data model."""
    
    DATA_TYPE_CHOICES = [
        ('OHLC', 'OHLC'),
        ('TRADE', 'Trade'),
        ('BID_ASK', 'Bid/Ask'),
        ('VOLUME', 'Volume'),
        ('GREEKS', 'Option Greeks'),
        ('IMPLIED_VOLATILITY', 'Implied Volatility'),
    ]
    
    INTERVAL_CHOICES = [
        ('1_MINUTE', '1 Minute'),
        ('5_MINUTE', '5 Minutes'),
        ('15_MINUTE', '15 Minutes'),
        ('30_MINUTE', '30 Minutes'),
        ('1_HOUR', '1 Hour'),
        ('4_HOUR', '4 Hours'),
        ('1_DAY', '1 Day'),
        ('1_WEEK', '1 Week'),
        ('1_MONTH', '1 Month'),
    ]
    
    # Core Information
    instrument = models.ForeignKey(
        'oms.Instrument',
        on_delete=models.CASCADE,
        related_name='historical_data',
        db_index=True
    )
    
    # Data Details
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, db_index=True)
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES, db_index=True)
    
    # Time Information
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    
    # OHLC Data
    open_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    close_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    
    # Volume and Other Data
    volume = models.BigIntegerField(null=True, blank=True)
    open_interest = models.BigIntegerField(null=True, blank=True)
    
    # Additional Data
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    source = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'marketdata_historical_data'
        verbose_name = _('historical data')
        verbose_name_plural = _('historical data')
        unique_together = ['instrument', 'data_type', 'interval', 'start_time']
        indexes = [
            models.Index(fields=['data_type']),
            models.Index(fields=['interval']),
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
            models.Index(fields=['instrument', 'data_type', 'interval', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.instrument.symbol} - {self.data_type} {self.interval} @ {self.start_time}"
