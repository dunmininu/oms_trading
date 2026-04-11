import pytest
from asgiref.sync import async_to_sync

from apps.brokers.models import Broker, BrokerConnection
from apps.brokers.services import BrokerService
from apps.marketdata.services import MarketDataService
from apps.oms.models import Instrument


@pytest.mark.django_db
class TestAsyncServiceBridges:
    """Verification suite for async/sync context safety in core services."""

    def test_market_data_ensure_instruments(self):
        """Verify that ensure_instruments works from a sync context (using bridges)."""
        # This will call the async method ensure_instruments which uses sync_to_async internally
        try:
            instruments = async_to_sync(MarketDataService.ensure_instruments)()
            assert len(instruments) == 2
            assert Instrument.objects.filter(symbol="GBPJPY").exists()
        except Exception as e:
            pytest.fail(f"Async Bridge Failed: {str(e)}")

    def test_broker_service_get_client(self):
        """Verify broker service can fetch client from sync context."""
        broker = Broker.objects.create(name="DERIV", broker_type="DERIV")
        conn = BrokerConnection.objects.create(
            broker=broker, name="Test Connection", api_key="test_token"
        )

        try:
            client = async_to_sync(BrokerService.get_client)(str(conn.id))
            assert client is not None
            assert client.token == "test_token"
        except Exception as e:
            pytest.fail(f"Broker Async Bridge Failed: {str(e)}")


@pytest.mark.django_db
def test_signal_log_persistence():
    """Verify SignalLog persistence logic."""
    from apps.strategies.models import SignalLog

    inst = Instrument.objects.create(symbol="V75", exchange="DERIV")

    SignalLog.objects.create(
        instrument=inst,
        strategy_name="Test Strategy",
        setup_type="ICT",
        grade="A+",
        message="A+ Setup Found",
    )

    assert SignalLog.objects.count() == 1
    assert SignalLog.objects.first().grade == "A+"
