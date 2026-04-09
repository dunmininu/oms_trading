"""
URL configuration for the API app.
"""

from django.urls import path, include
from .ninja_api import api
from .views.dashboard import DashboardIndexView, BacktestListView, StrategyListView

dashboard_urls = ([
    path('', DashboardIndexView.as_view(), name='index'),
    path('backtests/', BacktestListView.as_view(), name='backtests'),
    path('strategies/', StrategyListView.as_view(), name='strategies'),
], 'dashboard')

from django.shortcuts import redirect

urlpatterns = [
    path("", lambda r: redirect('dashboard:index')),
    path("api/", api.urls),
    path("dashboard/", include(dashboard_urls)),
]
