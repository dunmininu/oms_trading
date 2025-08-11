"""
Tenant models for multi-tenancy support.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

from apps.core.models import BaseModel


class Tenant(BaseModel):
    """Tenant model for multi-tenancy support."""
    
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    subdomain = models.CharField(max_length=50, unique=True, db_index=True, help_text='Subdomain for tenant-specific URLs')
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('INDIVIDUAL', 'Individual'),
            ('PARTNERSHIP', 'Partnership'),
            ('LLC', 'Limited Liability Company'),
            ('CORPORATION', 'Corporation'),
            ('HEDGE_FUND', 'Hedge Fund'),
            ('FAMILY_OFFICE', 'Family Office'),
            ('PROP_TRADING', 'Proprietary Trading'),
            ('OTHER', 'Other'),
        ],
        default='INDIVIDUAL'
    )
    tax_id = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    
    # Trading Configuration
    default_currency = models.CharField(
        max_length=3,
        default='USD',
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{3}$',
                message='Currency code must be 3 uppercase letters'
            )
        ]
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text='Timezone for the tenant (e.g., America/New_York)'
    )
    
    # Subscription and Limits
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('FREE', 'Free'),
            ('BASIC', 'Basic'),
            ('PROFESSIONAL', 'Professional'),
            ('ENTERPRISE', 'Enterprise'),
        ],
        default='FREE'
    )
    max_users = models.PositiveIntegerField(default=1)
    max_strategies = models.PositiveIntegerField(default=5)
    max_orders_per_day = models.PositiveIntegerField(default=100)
    
    # Status and Settings
    is_active = models.BooleanField(default=True, db_index=True)
    is_suspended = models.BooleanField(default=False, db_index=True)
    suspension_reason = models.TextField(blank=True)
    
    # Trial and Billing
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = _('tenant')
        verbose_name_plural = _('tenants')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.display_name or self.name
    
    def clean(self):
        """Validate the model."""
        from django.core.exceptions import ValidationError
        
        if self.trial_ends_at and self.subscription_ends_at:
            if self.trial_ends_at > self.subscription_ends_at:
                raise ValidationError(_('Trial end date cannot be after subscription end date.'))
    
    @property
    def is_trial_active(self):
        """Check if the tenant is in trial period."""
        if not self.trial_ends_at:
            return False
        from django.utils import timezone
        return timezone.now() < self.trial_ends_at
    
    @property
    def is_subscription_active(self):
        """Check if the tenant has an active subscription."""
        if not self.subscription_ends_at:
            return True
        from django.utils import timezone
        return timezone.now() < self.subscription_ends_at
    
    @property
    def can_use_system(self):
        """Check if the tenant can use the system."""
        return (
            self.is_active and 
            not self.is_suspended and 
            (self.is_trial_active or self.is_subscription_active)
        )


class TenantUser(BaseModel):
    """Relationship between users and tenants with roles."""
    
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('ADMIN', 'Administrator'),
        ('TRADER', 'Trader'),
        ('VIEWER', 'Viewer'),
        ('ANALYST', 'Analyst'),
        ('RISK_MANAGER', 'Risk Manager'),
        ('COMPLIANCE', 'Compliance Officer'),
    ]
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='tenant_users',
        db_index=True
    )
    user = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='tenant_memberships',
        db_index=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TRADER')
    
    # Permissions
    can_trade = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_strategies = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_manage_risk = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_users'
    )
    
    # Settings
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'tenants_tenant_user'
        verbose_name = _('tenant user')
        verbose_name_plural = _('tenant users')
        unique_together = ['tenant', 'user']
        indexes = [
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        """Override save to set permissions based on role."""
        if self.role == 'OWNER':
            self.can_trade = True
            self.can_manage_users = True
            self.can_manage_strategies = True
            self.can_view_reports = True
            self.can_manage_risk = True
        elif self.role == 'ADMIN':
            self.can_trade = True
            self.can_manage_users = True
            self.can_manage_strategies = True
            self.can_view_reports = True
            self.can_manage_risk = True
        elif self.role == 'TRADER':
            self.can_trade = True
            self.can_manage_users = False
            self.can_manage_strategies = True
            self.can_view_reports = True
            self.can_manage_risk = False
        elif self.role == 'RISK_MANAGER':
            self.can_trade = False
            self.can_manage_users = False
            self.can_manage_strategies = False
            self.can_view_reports = True
            self.can_manage_risk = True
        elif self.role == 'COMPLIANCE':
            self.can_trade = False
            self.can_manage_users = False
            self.can_manage_strategies = False
            self.can_view_reports = True
            self.can_manage_risk = False
        
        super().save(*args, **kwargs)


class TenantInvitation(BaseModel):
    """Invitation system for adding users to tenants."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('EXPIRED', 'Expired'),
    ]
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invitations',
        db_index=True
    )
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=TenantUser.ROLE_CHOICES, default='TRADER')
    invited_by = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    
    # Invitation details
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Response tracking
    responded_at = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True)
    
    # Email tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenants_tenant_invitation'
        verbose_name = _('tenant invitation')
        verbose_name_plural = _('tenant invitations')
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.tenant.name}"
    
    @property
    def is_expired(self):
        """Check if the invitation has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def accept(self, user):
        """Accept the invitation and create tenant user."""
        from django.utils import timezone
        
        if self.status != 'PENDING':
            raise ValueError('Invitation cannot be accepted')
        
        if self.is_expired:
            self.status = 'EXPIRED'
            self.save()
            raise ValueError('Invitation has expired')
        
        # Create tenant user
        TenantUser.objects.create(
            tenant=self.tenant,
            user=user,
            role=self.role,
            invited_by=self.invited_by
        )
        
        # Update invitation status
        self.status = 'ACCEPTED'
        self.responded_at = timezone.now()
        self.save()
    
    def decline(self, notes=''):
        """Decline the invitation."""
        if self.status != 'PENDING':
            raise ValueError('Invitation cannot be declined')
        
        self.status = 'DECLINED'
        self.responded_at = timezone.now()
        self.response_notes = notes
        self.save()
