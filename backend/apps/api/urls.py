"""
URL configuration for the API app.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from .ninja_api import api
from .views.dashboard import (
    BacktestListView,
    BrokerManagementView,
    BrokerOpsView,
    DashboardIndexView,
    MLDashboardView,
    StrategyListView,
    SystemSettingsView,
    TradeManagementView,
    ml_training_logs,
    telemetry_data,
)

dashboard_urls = (
    [
        path("", DashboardIndexView.as_view(), name="index"),
        path("telemetry/", telemetry_data, name="telemetry"),
        path("backtests/", BacktestListView.as_view(), name="backtests"),
        path("strategies/", StrategyListView.as_view(), name="strategies"),
        path("brokers/", BrokerManagementView.as_view(), name="brokers"),
        path("broker-ops/", BrokerOpsView.as_view(), name="broker_ops"),
        path("ml/", MLDashboardView.as_view(), name="ml"),
        path("ml-logs/<str:symbol>/", ml_training_logs, name="ml_logs"),
        path("trades/", TradeManagementView.as_view(), name="trades"),
        path("settings/", SystemSettingsView.as_view(), name="settings"),
    ],
    "dashboard",
)

urlpatterns = [
    path("", lambda r: redirect("dashboard:index")),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("dashboard/", include(dashboard_urls)),
]
