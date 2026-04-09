from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Avg
from apps.oms.models import Position, Order
from apps.strategies.models import SetupPerformance, BacktestResult, Strategy

class DashboardIndexView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_positions = Position.objects.exclude(quantity=0).select_related('instrument')
        unrealized_pnl = active_positions.aggregate(total=Sum('unrealized_pnl'))['total'] or 0
        total_exposure = active_positions.aggregate(total=Sum('market_value'))['total'] or 0

        setup_performances = SetupPerformance.objects.all().order_by('-total_pnl')

        # Recalculate avg_win_rate properly
        total_trades = sum(p.total_trades for p in setup_performances)
        total_wins = sum(p.winning_trades for p in setup_performances)
        avg_win_rate = (total_wins * 100 / total_trades) if total_trades > 0 else 0

        context.update({
            'active_positions': active_positions,
            'unrealized_pnl': round(unrealized_pnl, 2),
            'total_exposure': round(total_exposure, 2),
            'avg_win_rate': round(avg_win_rate, 2),
            'recent_orders': Order.objects.all().select_related('instrument').order_by('-created_at')[:10],
            'setup_performances': setup_performances,
            'strategies': Strategy.objects.all()
        })
        return context

class BacktestListView(ListView):
    model = BacktestResult
    template_name = "dashboard/backtests.html"
    context_object_name = "backtests"
    ordering = ["-created_at"]

class StrategyListView(ListView):
    model = Strategy
    template_name = "dashboard/strategies.html"
    context_object_name = "strategies"
