"""
Strategy models for managing trading strategies.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import BaseModel, TenantAwareModel


class Strategy(BaseModel):
    """Trading strategy model."""
    
    STRATEGY_TYPE_CHOICES = [
        ('MEAN_REVERSION', 'Mean Reversion'),
        ('MOMENTUM', 'Momentum'),
        ('ARBITRAGE', 'Arbitrage'),
        ('PAIRS_TRADING', 'Pairs Trading'),
        ('GRID_TRADING', 'Grid Trading'),
        ('SCALPING', 'Scalping'),
        ('SWING_TRADING', 'Swing Trading'),
        ('OPTIONS_STRATEGY', 'Options Strategy'),
        ('QUANTITATIVE', 'Quantitative'),
        ('CUSTOM', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('STOPPED', 'Stopped'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Core Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='strategies',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='strategies',
        db_index=True
    )
    
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPE_CHOICES, db_index=True)
    version = models.CharField(max_length=20, default='1.0.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    
    # Risk Management
    max_position_size = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_daily_loss = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_drawdown = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))]
    )
    
    # Execution Settings
    is_active = models.BooleanField(default=False, db_index=True)
    auto_start = models.BooleanField(default=False)
    paper_trading_only = models.BooleanField(default=True)
    
    # Schedule
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Performance Tracking
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_trades = models.PositiveIntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'strategies_strategy'
        verbose_name = _('strategy')
        verbose_name_plural = _('strategies')
        unique_together = ['tenant', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['strategy_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def clean(self):
        """Validate strategy configuration."""
        if self.max_drawdown and self.max_drawdown > 100:
            raise ValidationError("Maximum drawdown cannot exceed 100%")
        
        if self.win_rate and (self.win_rate < 0 or self.win_rate > 100):
            raise ValidationError("Win rate must be between 0 and 100")


class StrategyRun(BaseModel):
    """Strategy execution run model."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('STOPPED', 'Stopped'),
        ('ERROR', 'Error'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Core Information
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='strategy_runs',
        db_index=True
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name='runs',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='strategy_runs',
        db_index=True
    )
    
    # Run Details
    run_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Execution Information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Performance
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_trades = models.PositiveIntegerField(default=0)
    winning_trades = models.PositiveIntegerField(default=0)
    losing_trades = models.PositiveIntegerField(default=0)
    
    # Risk Metrics
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Configuration
    config_snapshot = models.JSONField(default=dict, blank=True)
    parameters_snapshot = models.JSONField(default=dict, blank=True)
    
    # Error Information
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Metadata
    logs = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'strategies_strategy_run'
        verbose_name = _('strategy run')
        verbose_name_plural = _('strategy runs')
        indexes = [
            models.Index(fields=['run_id']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['strategy', 'started_at']),
            models.Index(fields=['user', 'started_at']),
        ]
    
    def __str__(self):
        return f"{self.strategy.name} - Run {self.run_id}"
    
    @property
    def win_rate(self):
        """Calculate win rate for this run."""
        if self.total_trades == 0:
            return Decimal('0.00')
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def is_active(self):
        """Check if run is currently active."""
        return self.status in ['PENDING', 'RUNNING', 'PAUSED']
    
    def start(self):
        """Start the strategy run."""
        if self.status != 'PENDING':
            raise ValidationError("Only pending runs can be started")
        
        self.status = 'RUNNING'
        self.started_at = timezone.now()
        self.save()
    
    def pause(self):
        """Pause the strategy run."""
        if self.status != 'RUNNING':
            raise ValidationError("Only running runs can be paused")
        
        self.status = 'PAUSED'
        self.save()
    
    def resume(self):
        """Resume the strategy run."""
        if self.status != 'PAUSED':
            raise ValidationError("Only paused runs can be resumed")
        
        self.status = 'RUNNING'
        self.save()
    
    def stop(self):
        """Stop the strategy run."""
        if self.status not in ['RUNNING', 'PAUSED']:
            raise ValidationError("Only active runs can be stopped")
        
        self.status = 'STOPPED'
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()
    
    def complete(self):
        """Mark the strategy run as completed."""
        if self.status not in ['RUNNING', 'PAUSED']:
            raise ValidationError("Only active runs can be completed")
        
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()
    
    def error(self, message, traceback=None):
        """Mark the strategy run as errored."""
        self.status = 'ERROR'
        self.error_message = message
        if traceback:
            self.error_traceback = traceback
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()


class StrategyPerformance(BaseModel):
    """Strategy performance tracking model."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='strategy_performances',
        db_index=True
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name='performances',
        db_index=True
    )
    
    # Date Information
    date = models.DateField(db_index=True)
    
    # Daily Performance
    daily_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    daily_trades = models.PositiveIntegerField(default=0)
    daily_volume = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Risk Metrics
    daily_drawdown = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    daily_var = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Cumulative Metrics
    cumulative_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cumulative_trades = models.PositiveIntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'strategies_strategy_performance'
        verbose_name = _('strategy performance')
        verbose_name_plural = _('strategy performances')
        unique_together = ['tenant', 'strategy', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['strategy', 'date']),
        ]
    
    def __str__(self):
        return f"{self.strategy.name} - {self.date}"
