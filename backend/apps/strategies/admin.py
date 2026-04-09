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
    list_display = ('name', 'strategy_type', 'status', 'is_active', 'total_pnl', 'win_rate', 'health_check')
    list_editable = ('status', 'is_active')
    list_filter = ('strategy_type', 'status', 'is_active')
    search_fields = ('name', 'description')
    actions = ['duplicate_strategy', 'activate_strategies', 'deactivate_strategies', 'reset_performance']

    def health_check(self, obj):
        if obj.is_active and obj.status == 'RUNNING':
            return format_html('<span style="color: green;">● ACTIVE</span>')
        return format_html('<span style="color: gray;">○ INACTIVE</span>')
    health_check.short_description = 'Status'

    def duplicate_strategy(self, request, queryset):
        for strategy in queryset:
            strategy.pk = None
            strategy.name = f"{strategy.name} (Copy)"
            strategy.save()
    duplicate_strategy.short_description = "Duplicate selected strategies"

    def activate_strategies(self, request, queryset):
        queryset.update(is_active=True, status='RUNNING')
    activate_strategies.short_description = "▶ Start selected strategies"

    def deactivate_strategies(self, request, queryset):
        queryset.update(is_active=False, status='STOPPED')
    deactivate_strategies.short_description = "⏹ Stop selected strategies"

    def reset_performance(self, request, queryset):
        queryset.update(total_pnl=0, total_trades=0, win_rate=0)
    reset_performance.short_description = "↺ Reset performance metrics"

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
        from django.db.models import Sum, Avg

        active_positions = Position.objects.exclude(quantity=0).select_related('instrument')
        unrealized_pnl = active_positions.aggregate(total=Sum('unrealized_pnl'))['total'] or 0
        total_exposure = active_positions.aggregate(total=Sum('market_value'))['total'] or 0

        # Calculate performance metrics
        setup_performances = SetupPerformance.objects.all().order_by('-total_pnl')
        avg_win_rate = setup_performances.aggregate(avg=Avg('success_rate'))['avg'] or 0

        context = {
            **self.admin_site.each_context(request),
            'title': 'Trading Command Center',
            'active_positions': active_positions,
            'unrealized_pnl': unrealized_pnl,
            'total_exposure': total_exposure,
            'avg_win_rate': round(avg_win_rate, 2),
            'recent_orders': Order.objects.all().select_related('instrument').order_by('-created_at')[:10],
            'setup_performances': setup_performances
        }
        return render(request, 'admin/trading_dashboard.html', context)
