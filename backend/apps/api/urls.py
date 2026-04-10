"""
URL configuration for the API app.
"""

from django.urls import path, include
from .ninja_api import api
from .views.dashboard import (
    DashboardIndexView, BacktestListView, StrategyListView,
    BrokerManagementView, SystemSettingsView
)

dashboard_urls = ([
    path('', DashboardIndexView.as_view(), name='index'),
    path('backtests/', BacktestListView.as_view(), name='backtests'),
    path('strategies/', StrategyListView.as_view(), name='strategies'),
    path('brokers/', BrokerManagementView.as_view(), name='brokers'),
    path('settings/', SystemSettingsView.as_view(), name='settings'),
], 'dashboard')

from django.shortcuts import redirect

urlpatterns = [
    path("", lambda r: redirect('dashboard:index')),
    path("api/", api.urls),
    path("dashboard/", include(dashboard_urls)),
]
