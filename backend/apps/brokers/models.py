"""
Broker models for managing broker connections and accounts.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel, TenantAwareModel


class Broker(BaseModel):
    """Broker model for managing different broker connections."""
    
    BROKER_TYPE_CHOICES = [
        ('INTERACTIVE_BROKERS', 'Interactive Brokers'),
        ('TD_AMERITRADE', 'TD Ameritrade'),
        ('CHARLES_SCHWAB', 'Charles Schwab'),
        ('ETRADE', 'E*TRADE'),
        ('FIDELITY', 'Fidelity'),
        ('ROBINHOOD', 'Robinhood'),
        ('ALPACA', 'Alpaca'),
        ('TRADIER', 'Tradier'),
        ('CUSTOM', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    display_name = models.CharField(max_length=200)
    broker_type = models.CharField(max_length=50, choices=BROKER_TYPE_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    
    # Connection Settings
    host = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    use_ssl = models.BooleanField(default=True)
    
    # API Configuration
    api_version = models.CharField(max_length=20, blank=True)
    timeout_seconds = models.PositiveIntegerField(default=30)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_testing = models.BooleanField(default=False, db_index=True)
    
    # Metadata
    website = models.URLField(blank=True)
    support_email = models.EmailField(blank=True)
    documentation_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'brokers_broker'
        verbose_name = _('broker')
        verbose_name_plural = _('brokers')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['broker_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_testing']),
        ]
    
    def __str__(self):
        return self.display_name or self.name


class BrokerConnection(BaseModel):
    """Broker connection for a specific tenant."""
    
    STATUS_CHOICES = [
        ('DISCONNECTED', 'Disconnected'),
        ('CONNECTING', 'Connecting'),
        ('CONNECTED', 'Connected'),
        ('ERROR', 'Error'),
        ('MAINTENANCE', 'Maintenance'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='broker_connections',
        db_index=True
    )
    broker = models.ForeignKey(
        Broker,
        on_delete=models.CASCADE,
        related_name='connections',
        db_index=True
    )
    
    # Connection Details
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    
    # Authentication
    username = models.CharField(max_length=100, blank=True)
    password_encrypted = models.TextField(blank=True)  # Encrypted password
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.TextField(blank=True)  # Encrypted secret
    access_token = models.TextField(blank=True)  # Encrypted token
    refresh_token = models.TextField(blank=True)  # Encrypted refresh token
    
    # Connection Settings
    host_override = models.CharField(max_length=255, blank=True)
    port_override = models.PositiveIntegerField(null=True, blank=True)
    use_ssl_override = models.BooleanField(null=True, blank=True)
    
    # Status and Health
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISCONNECTED', db_index=True)
    last_connected = models.DateTimeField(null=True, blank=True)
    last_disconnected = models.DateTimeField(null=True, blank=True)
    connection_errors = models.JSONField(default=list, blank=True)
    
    # Trading Hours
    trading_hours_start = models.TimeField(null=True, blank=True)
    trading_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Risk Management
    max_order_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_daily_loss = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Settings
    auto_reconnect = models.BooleanField(default=True)
    heartbeat_interval = models.PositiveIntegerField(default=30)  # seconds
    enable_logging = models.BooleanField(default=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'brokers_broker_connection'
        verbose_name = _('broker connection')
        verbose_name_plural = _('broker connections')
        unique_together = ['tenant', 'broker', 'name']
        indexes = [
            models.Index(fields=['tenant', 'broker']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['status', 'last_connected']),
            models.Index(fields=['broker', 'status']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.broker.name} ({self.name})"
    
    @property
    def is_connected(self):
        """Check if the connection is currently active."""
        return self.status == 'CONNECTED'
    
    @property
    def can_trade(self):
        """Check if the connection can be used for trading."""
        return (
            self.is_connected and 
            self.is_active and 
            self.tenant.can_use_system
        )
    
    def get_connection_settings(self):
        """Get connection settings with overrides."""
        settings = {
            'host': self.host_override or self.broker.host,
            'port': self.port_override or self.broker.port,
            'use_ssl': self.use_ssl_override if self.use_ssl_override is not None else self.broker.use_ssl,
            'timeout': self.broker.timeout_seconds,
            'max_retries': self.broker.max_retries,
        }
        return {k: v for k, v in settings.items() if v is not None}


class BrokerAccount(BaseModel):
    """Broker account information."""
    
    ACCOUNT_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('JOINT', 'Joint'),
        ('IRA', 'Individual Retirement Account'),
        ('401K', '401(k)'),
        ('TRUST', 'Trust'),
        ('CORPORATE', 'Corporate'),
        ('PARTNERSHIP', 'Partnership'),
        ('LLC', 'Limited Liability Company'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
        ('PENDING', 'Pending'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='broker_accounts',
        db_index=True
    )
    broker_connection = models.ForeignKey(
        BrokerConnection,
        on_delete=models.CASCADE,
        related_name='accounts',
        db_index=True
    )
    
    # Account Information
    account_number = models.CharField(max_length=100, db_index=True)
    account_name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    
    # Account Details
    currency = models.CharField(max_length=3, default='USD')
    base_currency = models.CharField(max_length=3, default='USD')
    
    # Trading Permissions
    can_trade_stocks = models.BooleanField(default=True)
    can_trade_options = models.BooleanField(default=False)
    can_trade_futures = models.BooleanField(default=False)
    can_trade_forex = models.BooleanField(default=False)
    can_trade_bonds = models.BooleanField(default=False)
    can_trade_mutual_funds = models.BooleanField(default=False)
    
    # Risk Profile
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('CONSERVATIVE', 'Conservative'),
            ('MODERATE', 'Moderate'),
            ('AGGRESSIVE', 'Aggressive'),
        ],
        default='MODERATE'
    )
    
    # Account Limits
    max_leverage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('1.00')), MaxValueValidator(Decimal('100.00'))]
    )
    day_trading_buying_power = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    overnight_buying_power = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'brokers_broker_account'
        verbose_name = _('broker account')
        verbose_name_plural = _('broker accounts')
        unique_together = ['tenant', 'broker_connection', 'account_number']
        indexes = [
            models.Index(fields=['tenant', 'broker_connection']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['account_number']),
            models.Index(fields=['status', 'can_trade_stocks']),
        ]
    
    def __str__(self):
        return f"{self.account_name} ({self.account_number})"
    
    @property
    def can_trade(self):
        """Check if the account can be used for trading."""
        return (
            self.status == 'ACTIVE' and
            self.broker_connection.can_trade and
            self.tenant.can_use_system
        )
    
    def get_trading_permissions(self):
        """Get available trading permissions."""
        permissions = []
        if self.can_trade_stocks:
            permissions.append('STOCKS')
        if self.can_trade_options:
            permissions.append('OPTIONS')
        if self.can_trade_futures:
            permissions.append('FUTURES')
        if self.can_trade_forex:
            permissions.append('FOREX')
        if self.can_trade_bonds:
            permissions.append('BONDS')
        if self.can_trade_mutual_funds:
            permissions.append('MUTUAL_FUNDS')
        return permissions


class BrokerConnectionLog(BaseModel):
    """Log of broker connection events."""
    
    EVENT_TYPE_CHOICES = [
        ('CONNECT', 'Connect'),
        ('DISCONNECT', 'Disconnect'),
        ('RECONNECT', 'Reconnect'),
        ('ERROR', 'Error'),
        ('HEARTBEAT', 'Heartbeat'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('API_CALL', 'API Call'),
        ('ORDER_PLACE', 'Order Place'),
        ('ORDER_CANCEL', 'Order Cancel'),
        ('ORDER_MODIFY', 'Order Modify'),
        ('EXECUTION', 'Execution'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='broker_connection_logs',
        db_index=True
    )
    broker_connection = models.ForeignKey(
        BrokerConnection,
        on_delete=models.CASCADE,
        related_name='connection_logs',
        db_index=True
    )
    
    # Event Details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_index=True)
    message = models.TextField()
    level = models.CharField(
        max_length=20,
        choices=[
            ('DEBUG', 'Debug'),
            ('INFO', 'Info'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical'),
        ],
        default='INFO'
    )
    
    # Request Details
    request_id = models.CharField(max_length=100, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error Details
    error_code = models.CharField(max_length=50, blank=True)
    error_details = models.JSONField(null=True, blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'brokers_broker_connection_log'
        verbose_name = _('broker connection log')
        verbose_name_plural = _('broker connection logs')
        indexes = [
            models.Index(fields=['tenant', 'broker_connection']),
            models.Index(fields=['tenant', 'event_type']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['level', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type}: {self.message[:50]}"
