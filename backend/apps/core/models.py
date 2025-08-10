"""
Core models and mixins for OMS Trading system.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class BaseModel(models.Model):
    """Base model with common fields for all models."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"


class TenantAwareModel(BaseModel):
    """Base model for tenant-scoped models."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        db_index=True
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'is_active']),
        ]


class User(AbstractUser, BaseModel):
    """Custom user model with UUID primary key."""
    
    # Override the default id field
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Remove username field, use email instead
    username = None
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    
    # Additional fields
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.URLField(blank=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_expires = models.DateTimeField(null=True, blank=True)
    
    # Password reset
    password_reset_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    
    # Last activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'core_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email
    
    def clean(self):
        """Validate the model."""
        super().clean()
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(_('Date of birth cannot be in the future.'))
    
    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)


class AuditLog(BaseModel):
    """Audit log for tracking all system activities."""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('API_CALL', 'API Call'),
        ('ORDER_PLACE', 'Order Place'),
        ('ORDER_CANCEL', 'Order Cancel'),
        ('ORDER_MODIFY', 'Order Modify'),
        ('EXECUTION', 'Execution'),
        ('POSITION_CHANGE', 'Position Change'),
        ('RISK_CHECK', 'Risk Check'),
        ('STRATEGY_START', 'Strategy Start'),
        ('STRATEGY_STOP', 'Strategy Stop'),
        ('BROKER_CONNECT', 'Broker Connect'),
        ('BROKER_DISCONNECT', 'Broker Disconnect'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, db_index=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_audit_log'
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        indexes = [
            models.Index(fields=['tenant', 'action']),
            models.Index(fields=['tenant', 'resource_type']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.resource_type} {self.resource_id}"


class SystemConfiguration(BaseModel):
    """System-wide configuration settings."""
    
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general', db_index=True)
    is_public = models.BooleanField(default=False, help_text='Whether this config is visible to all users')
    
    class Meta:
        db_table = 'core_system_configuration'
        verbose_name = _('system configuration')
        verbose_name_plural = _('system configurations')
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    @classmethod
    def get_value(cls, key: str, default=None):
        """Get configuration value by key."""
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, key: str, value, description='', category='general', is_public=False):
        """Set configuration value by key."""
        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'category': category,
                'is_public': is_public,
                'is_active': True,
            }
        )
        return config


class HealthCheck(BaseModel):
    """Health check records for monitoring."""
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    COMPONENT_CHOICES = [
        ('DATABASE', 'Database'),
        ('REDIS', 'Redis'),
        ('CELERY', 'Celery'),
        ('IB_CONNECTOR', 'IB Connector'),
        ('MARKET_DATA', 'Market Data'),
        ('RISK_ENGINE', 'Risk Engine'),
        ('ORDER_ROUTER', 'Order Router'),
        ('WEBHOOK_SENDER', 'Webhook Sender'),
    ]
    
    component = models.CharField(max_length=50, choices=COMPONENT_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    message = models.TextField()
    response_time_ms = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    error_traceback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'core_health_check'
        verbose_name = _('health check')
        verbose_name_plural = _('health checks')
        indexes = [
            models.Index(fields=['component', 'status']),
            models.Index(fields=['component', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.component}: {self.status} - {self.message}"
