"""
Django admin configuration for core models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    User, AuditLog, SystemConfiguration, HealthCheck
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    list_display = [
        'email', 'first_name', 'last_name', 'is_active', 
        'email_verified', 'two_factor_enabled', 'last_activity', 'created_at'
    ]
    list_filter = [
        'is_active', 'email_verified', 'two_factor_enabled', 
        'is_staff', 'is_superuser', 'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Security'), {
            'fields': (
                'email_verified', 'two_factor_enabled', 'last_activity', 'last_ip_address'
            ),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['last_activity', 'last_ip_address', 'date_joined', 'last_login']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AuditLog model."""
    
    list_display = [
        'action', 'resource_type', 'resource_id', 'user', 'tenant_id',
        'ip_address', 'created_at'
    ]
    list_filter = [
        'action', 'resource_type', 'created_at'
    ]
    search_fields = ['action', 'resource_type', 'resource_id', 'user__email']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'action', 'resource_type', 
        'resource_id', 'old_values', 'new_values', 'ip_address', 
        'user_agent', 'session_id', 'request_id', 'metadata'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('action', 'resource_type', 'resource_id', 'tenant', 'user')
        }),
        (_('Values'), {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
        (_('Request Details'), {
            'fields': ('ip_address', 'user_agent', 'session_id', 'request_id'),
            'classes': ('collapse',)
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
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'tenant')
    
    def has_add_permission(self, request):
        """Audit logs should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs should not be deleted."""
        return False


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin configuration for SystemConfiguration model."""
    
    list_display = ['key', 'category', 'is_public', 'is_active', 'updated_at']
    list_filter = ['category', 'is_public', 'is_active']
    search_fields = ['key', 'description']
    ordering = ['category', 'key']
    
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'category', 'is_public')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make key readonly for existing objects."""
        if obj:
            return ['key']
        return []
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request)


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    """Admin configuration for HealthCheck model."""
    
    list_display = [
        'component', 'status', 'response_time_display', 'created_at'
    ]
    list_filter = ['component', 'status', 'created_at']
    search_fields = ['component', 'message']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'component', 'status', 
        'message', 'response_time_ms', 'details', 'error_traceback'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('component', 'status', 'message')
        }),
        (_('Performance'), {
            'fields': ('response_time_ms', 'details'),
            'classes': ('collapse',)
        }),
        (_('Error Details'), {
            'fields': ('error_traceback',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def response_time_display(self, obj):
        """Display response time with color coding."""
        if obj.response_time_ms is None:
            return '-'
        
        if obj.response_time_ms < 100:
            color = 'green'
        elif obj.response_time_ms < 500:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{}ms</span>',
            color,
            obj.response_time_ms
        )
    response_time_display.short_description = _('Response Time')
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        """Health checks should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Health checks should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Health checks should not be deleted."""
        return False
