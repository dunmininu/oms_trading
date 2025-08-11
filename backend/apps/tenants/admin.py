"""
Django admin configuration for tenant models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Tenant, TenantUser, TenantInvitation


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin configuration for Tenant model."""
    
    list_display = [
        'name', 'display_name', 'business_type', 'subscription_plan', 
        'status_display', 'user_count', 'created_at'
    ]
    list_filter = [
        'business_type', 'subscription_plan', 'is_active', 'is_suspended',
        'country', 'created_at'
    ]
    search_fields = ['name', 'display_name', 'contact_email', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'user_count']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'display_name', 'description')
        }),
        (_('Contact Information'), {
            'fields': ('contact_email', 'contact_phone', 'website')
        }),
        (_('Address'), {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state', 
                'postal_code', 'country'
            ),
            'classes': ('collapse',)
        }),
        (_('Business Information'), {
            'fields': ('business_type', 'tax_id', 'registration_number')
        }),
        (_('Trading Configuration'), {
            'fields': ('default_currency', 'timezone')
        }),
        (_('Subscription and Limits'), {
            'fields': (
                'subscription_plan', 'max_users', 'max_strategies', 
                'max_orders_per_day', 'trial_ends_at', 'subscription_ends_at'
            )
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_suspended', 'suspension_reason')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display tenant status with color coding."""
        if obj.is_suspended:
            return format_html(
                '<span style="color: red;">Suspended</span>'
            )
        elif not obj.is_active:
            return format_html(
                '<span style="color: orange;">Inactive</span>'
            )
        elif obj.is_trial_active:
            return format_html(
                '<span style="color: blue;">Trial</span>'
            )
        elif obj.is_subscription_active:
            return format_html(
                '<span style="color: green;">Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">Expired</span>'
            )
    status_display.short_description = _('Status')
    
    def user_count(self, obj):
        """Display count of active users."""
        count = obj.tenant_users.filter(is_active=True).count()
        return count
    user_count.short_description = _('Users')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        return super().get_queryset(request).prefetch_related('tenant_users')


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Admin configuration for TenantUser model."""
    
    list_display = [
        'user_email', 'tenant_name', 'role', 'permissions_display', 
        'is_active', 'joined_at'
    ]
    list_filter = [
        'role', 'is_active', 'can_trade', 'can_manage_users', 
        'can_manage_strategies', 'can_manage_risk', 'joined_at'
    ]
    search_fields = ['user__email', 'tenant__name', 'tenant__display_name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'joined_at', 'invited_by'
    ]
    ordering = ['-joined_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tenant', 'user', 'role')
        }),
        (_('Permissions'), {
            'fields': (
                'can_trade', 'can_manage_users', 'can_manage_strategies',
                'can_view_reports', 'can_manage_risk'
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Invitation'), {
            'fields': ('invited_by', 'joined_at'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('notification_preferences',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email with link to user admin."""
        if obj.user:
            url = reverse('admin:core_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def tenant_name(self, obj):
        """Display tenant name with link to tenant admin."""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return '-'
    tenant_name.short_description = _('Tenant')
    tenant_name.admin_order_field = 'tenant__name'
    
    def permissions_display(self, obj):
        """Display permissions as badges."""
        badges = []
        if obj.can_trade:
            badges.append('<span style="background: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Trade</span>')
        if obj.can_manage_users:
            badges.append('<span style="background: blue; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Users</span>')
        if obj.can_manage_strategies:
            badges.append('<span style="background: purple; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Strategies</span>')
        if obj.can_manage_risk:
            badges.append('<span style="background: orange; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Risk</span>')
        
        return mark_safe(' '.join(badges)) if badges else '-'
    permissions_display.short_description = _('Permissions')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'tenant', 'invited_by')


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    """Admin configuration for TenantInvitation model."""
    
    list_display = [
        'email', 'tenant_name', 'role', 'invited_by_email', 'status', 
        'expires_at', 'created_at'
    ]
    list_filter = [
        'role', 'status', 'tenant', 'created_at', 'expires_at'
    ]
    search_fields = ['email', 'tenant__name', 'invited_by__email']
    readonly_fields = [
        'id', 'token', 'created_at', 'updated_at', 'sent_at', 'opened_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tenant', 'email', 'role', 'invited_by')
        }),
        (_('Invitation Details'), {
            'fields': ('token', 'expires_at', 'status')
        }),
        (_('Response'), {
            'fields': ('responded_at', 'response_notes'),
            'classes': ('collapse',)
        }),
        (_('Email Tracking'), {
            'fields': ('sent_at', 'opened_at'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tenant_name(self, obj):
        """Display tenant name with link to tenant admin."""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return '-'
    tenant_name.short_description = _('Tenant')
    tenant_name.admin_order_field = 'tenant__name'
    
    def invited_by_email(self, obj):
        """Display invited by email with link to user admin."""
        if obj.invited_by:
            url = reverse('admin:core_user_change', args=[obj.invited_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.invited_by.email)
        return '-'
    invited_by_email.short_description = _('Invited By')
    invited_by_email.admin_order_field = 'invited_by__email'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('tenant', 'invited_by')
    
    def has_change_permission(self, request, obj=None):
        """Only allow changing status and response fields."""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of invitations."""
        return True
