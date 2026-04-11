import pytest
from django.test import Client
from django.urls import reverse

from apps.brokers.models import Broker, BrokerConnection


@pytest.mark.django_db
class TestDashboardViews:
    """Integration tests for dashboard view actions."""

    def setup_method(self):
        self.client = Client()
        # No tenant logic required anymore

    def test_backtest_list_view_get(self):
        url = reverse("dashboard:backtests")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Strategy Backtesting" in response.content

    def test_strategies_view_get(self):
        url = reverse("dashboard:strategies")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Strategy Fleet" in response.content
        assert b"Intelligence Signal Feed" in response.content

    def test_broker_management_actions(self):
        """Test broker connection actions."""
        broker = Broker.objects.create(name="DERIV", broker_type="DERIV")
        conn = BrokerConnection.objects.create(
            broker=broker, name="Deriv Connection", api_key="test_key"
        )

        url = reverse("dashboard:brokers")

        # Test Disconnect
        response = self.client.post(
            url, {"action": "disconnect", "connection_id": str(conn.id)}
        )
        assert response.status_code == 200
        conn.refresh_from_db()
        assert conn.status == "DISCONNECTED"

        # Add Deriv Key
        response = self.client.post(
            url, {"action": "add_deriv_key", "deriv_token": "new_test_token"}
        )
        assert response.status_code == 200
        assert BrokerConnection.objects.filter(api_key="new_test_token").exists()
