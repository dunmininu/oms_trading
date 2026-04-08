"""
Custom Django Admin configuration for strategy and performance monitoring.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from .models import Strategy, StrategyRun, SetupPerformance, StrategyPerformance

@admin.register(SetupPerformance)
class SetupPerformanceAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'setup_type', 'timeframe', 'total_trades', 'success_rate_display', 'total_pnl')
    list_filter = ('instrument', 'setup_type', 'timeframe')

    def success_rate_display(self, obj):
        color = 'green' if obj.success_rate > 50 else 'red'
        return format_html('<b style="color: {};">{}%</b>', color, obj.success_rate)
    success_rate_display.short_description = 'Success Rate'

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy_type', 'status', 'is_active', 'total_pnl', 'win_rate')
    list_editable = ('status', 'is_active')
    actions = ['duplicate_strategy']

    def duplicate_strategy(self, request, queryset):
        for strategy in queryset:
            strategy.pk = None
            strategy.name = f"{strategy.name} (Copy)"
            strategy.save()
    duplicate_strategy.short_description = "Duplicate selected strategies"

@admin.register(StrategyRun)
class StrategyRunAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'strategy', 'status', 'started_at', 'total_pnl', 'total_trades')
    list_filter = ('status', 'strategy')
    readonly_fields = ('run_id', 'started_at', 'completed_at', 'duration_seconds')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='trading_dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """Custom dashboard with PnL and setup metrics."""
        from apps.oms.models import Position, Order
        context = {
            **self.admin_site.each_context(request),
            'title': 'Trading Command Center',
            'active_positions': Position.objects.exclude(quantity=0),
            'recent_orders': Order.objects.all().order_by('-created_at')[:10],
            'setup_performances': SetupPerformance.objects.all().order_by('-total_pnl')
        }
        return render(request, 'admin/trading_dashboard.html', context)
