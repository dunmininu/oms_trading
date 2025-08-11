"""
Django admin configuration for broker models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Broker, BrokerConnection, BrokerAccount, BrokerConnectionLog


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    """Admin configuration for Broker model."""
    
    list_display = [
        'name', 'display_name', 'broker_type', 'status_display', 
        'connection_count', 'created_at'
    ]
    list_filter = [
        'broker_type', 'is_active', 'is_testing', 'created_at'
    ]
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'connection_count']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'display_name', 'broker_type', 'description')
        }),
        (_('Connection Settings'), {
            'fields': ('host', 'port', 'use_ssl')
        }),
        (_('API Configuration'), {
            'fields': ('api_version', 'timeout_seconds', 'max_retries')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_testing')
        }),
        (_('Contact Information'), {
            'fields': ('website', 'support_email', 'documentation_url'),
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
    
    def status_display(self, obj):
        """Display broker status with color coding."""
        if obj.is_testing:
            return format_html(
                '<span style="color: orange;">Testing</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="color: green;">Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">Inactive</span>'
            )
    status_display.short_description = _('Status')
    
    def connection_count(self, obj):
        """Display count of active connections."""
        count = obj.connections.filter(is_active=True).count()
        return count
    connection_count.short_description = _('Connections')
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).prefetch_related('connections')


@admin.register(BrokerConnection)
class BrokerConnectionAdmin(admin.ModelAdmin):
    """Admin configuration for BrokerConnection model."""
    
    list_display = [
        'name', 'tenant_name', 'broker_name', 'status_display', 
        'last_connected', 'created_at'
    ]
    list_filter = [
        'status', 'broker__broker_type', 'auto_reconnect', 'enable_logging',
        'tenant', 'created_at'
    ]
    search_fields = ['name', 'tenant__name', 'broker__name', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_connected', 'last_disconnected'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tenant', 'broker', 'name', 'description')
        }),
        (_('Authentication'), {
            'fields': (
                'username', 'password_encrypted', 'api_key', 'api_secret',
                'access_token', 'refresh_token'
            ),
            'classes': ('collapse',)
        }),
        (_('Connection Settings'), {
            'fields': ('host_override', 'port_override', 'use_ssl_override')
        }),
        (_('Status and Health'), {
            'fields': ('status', 'connection_errors')
        }),
        (_('Trading Hours'), {
            'fields': ('trading_hours_start', 'trading_hours_end', 'timezone'),
            'classes': ('collapse',)
        }),
        (_('Risk Management'), {
            'fields': ('max_order_value', 'max_daily_loss'),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': ('auto_reconnect', 'heartbeat_interval', 'enable_logging')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'last_connected', 'last_disconnected'),
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
    
    def broker_name(self, obj):
        """Display broker name with link to broker admin."""
        if obj.broker:
            url = reverse('admin:brokers_broker_change', args=[obj.broker.id])
            return format_html('<a href="{}">{}</a>', url, obj.broker.name)
        return '-'
    broker_name.short_description = _('Broker')
    broker_name.admin_order_field = 'broker__name'
    
    def status_display(self, obj):
        """Display connection status with color coding."""
        status_colors = {
            'CONNECTED': 'green',
            'CONNECTING': 'blue',
            'DISCONNECTED': 'gray',
            'ERROR': 'red',
            'MAINTENANCE': 'orange',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Status')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('tenant', 'broker')


@admin.register(BrokerAccount)
class BrokerAccountAdmin(admin.ModelAdmin):
    """Admin configuration for BrokerAccount model."""
    
    list_display = [
        'account_name', 'account_number', 'tenant_name', 'broker_connection_name',
        'account_type', 'status_display', 'permissions_display', 'created_at'
    ]
    list_filter = [
        'account_type', 'status', 'risk_tolerance', 'can_trade_stocks',
        'can_trade_options', 'can_trade_futures', 'tenant', 'created_at'
    ]
    search_fields = [
        'account_name', 'account_number', 'tenant__name', 
        'broker_connection__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tenant', 'broker_connection', 'account_name', 'account_number')
        }),
        (_('Account Details'), {
            'fields': ('account_type', 'status', 'currency', 'base_currency')
        }),
        (_('Trading Permissions'), {
            'fields': (
                'can_trade_stocks', 'can_trade_options', 'can_trade_futures',
                'can_trade_forex', 'can_trade_bonds', 'can_trade_mutual_funds'
            )
        }),
        (_('Risk Profile'), {
            'fields': ('risk_tolerance', 'max_leverage')
        }),
        (_('Account Limits'), {
            'fields': ('day_trading_buying_power', 'overnight_buying_power'),
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
    
    def tenant_name(self, obj):
        """Display tenant name with link to tenant admin."""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return '-'
    tenant_name.short_description = _('Tenant')
    tenant_name.admin_order_field = 'tenant__name'
    
    def broker_connection_name(self, obj):
        """Display broker connection name with link to admin."""
        if obj.broker_connection:
            url = reverse('admin:brokers_brokerconnection_change', args=[obj.broker_connection.id])
            return format_html('<a href="{}">{}</a>', url, obj.broker_connection.name)
        return '-'
    broker_connection_name.short_description = _('Broker Connection')
    broker_connection_name.admin_order_field = 'broker_connection__name'
    
    def status_display(self, obj):
        """Display account status with color coding."""
        status_colors = {
            'ACTIVE': 'green',
            'INACTIVE': 'gray',
            'SUSPENDED': 'red',
            'CLOSED': 'black',
            'PENDING': 'orange',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Status')
    
    def permissions_display(self, obj):
        """Display trading permissions as badges."""
        badges = []
        if obj.can_trade_stocks:
            badges.append('<span style="background: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Stocks</span>')
        if obj.can_trade_options:
            badges.append('<span style="background: blue; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Options</span>')
        if obj.can_trade_futures:
            badges.append('<span style="background: purple; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Futures</span>')
        if obj.can_trade_forex:
            badges.append('<span style="background: orange; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Forex</span>')
        
        return mark_safe(' '.join(badges)) if badges else '-'
    permissions_display.short_description = _('Permissions')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('tenant', 'broker_connection')


@admin.register(BrokerConnectionLog)
class BrokerConnectionLogAdmin(admin.ModelAdmin):
    """Admin configuration for BrokerConnectionLog model."""
    
    list_display = [
        'event_type', 'tenant_name', 'broker_connection_name', 'level_display',
        'message_preview', 'response_time_display', 'created_at'
    ]
    list_filter = [
        'event_type', 'level', 'tenant', 'broker_connection', 'created_at'
    ]
    search_fields = [
        'message', 'tenant__name', 'broker_connection__name', 'error_code'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'event_type', 'message', 'level',
        'request_id', 'response_time_ms', 'error_code', 'error_details', 'stack_trace'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tenant', 'broker_connection', 'event_type', 'message', 'level')
        }),
        (_('Request Details'), {
            'fields': ('request_id', 'response_time_ms'),
            'classes': ('collapse',)
        }),
        (_('Error Details'), {
            'fields': ('error_code', 'error_details', 'stack_trace'),
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
    
    def tenant_name(self, obj):
        """Display tenant name with link to tenant admin."""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return '-'
    tenant_name.short_description = _('Tenant')
    tenant_name.admin_order_field = 'tenant__name'
    
    def broker_connection_name(self, obj):
        """Display broker connection name with link to admin."""
        if obj.broker_connection:
            url = reverse('admin:brokers_brokerconnection_change', args=[obj.broker_connection.id])
            return format_html('<a href="{}">{}</a>', url, obj.broker_connection.name)
        return '-'
    broker_connection_name.short_description = _('Broker Connection')
    broker_connection_name.admin_order_field = 'broker_connection__name'
    
    def level_display(self, obj):
        """Display log level with color coding."""
        level_colors = {
            'DEBUG': 'gray',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'darkred',
        }
        color = level_colors.get(obj.level, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.level
        )
    level_display.short_description = _('Level')
    
    def message_preview(self, obj):
        """Display truncated message."""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = _('Message')
    
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
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('tenant', 'broker_connection')
    
    def has_add_permission(self, request):
        """Connection logs should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Connection logs should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Connection logs should not be deleted."""
        return False
