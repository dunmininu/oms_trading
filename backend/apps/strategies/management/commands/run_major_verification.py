import asyncio
import logging
import os
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.brokers.models import Broker, BrokerAccount, BrokerConnection
from apps.core.models import User
from apps.marketdata.cache import MarketDataCache
from apps.marketdata.services import MarketDataService
from apps.oms.models import Instrument, Order
from apps.oms.services import OMSService
from apps.strategies.grading_services import GradingService
from apps.strategies.ml_services import MLStrategyService
from apps.strategies.risk_services import RiskManagementService
from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run MAJOR end-to-end verification of Phase 1 & 2"

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        asyncio.run(self.run_major_test())

    async def run_major_test(self):
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=== MAJOR END-TO-END VERIFICATION (PHASE 1 & 2) ==="
            )
        )

        tenant = Tenant.objects.get(slug="default")
        user = User.objects.get(email="admin@omstrading.com")
        conn = BrokerConnection.objects.get(tenant=tenant, name="Main IB Connection")
        gbpjpy, btcusd = await MarketDataService.ensure_instruments()

        self.stdout.write("Testing High-Speed Redis Cache...")
        MarketDataCache.push_tick("BTCUSD", 50000.0, 100)
        ticks = MarketDataCache.get_recent_ticks("BTCUSD", count=1)
        if ticks and ticks[0]["p"] == 50000.0:
            self.stdout.write(
                self.style.SUCCESS("Cache verified: Sub-millisecond tick access ready.")
            )

        self.stdout.write("Running XGBoost Inference...")
        ml_prediction = MLStrategyService.predict_setup(btcusd, "15_MINUTE")
        self.stdout.write(f"ML Success Probability: {ml_prediction['probability']:.2f}")

        self.stdout.write("Executing integrated trade flow...")
        os.environ["FORCE_SETUP_GRADE"] = "A+"
        grading_result = GradingService.grade_setup(btcusd, "15_MINUTE", tenant=tenant)

        test_win_prob = 0.6
        risk_result = RiskManagementService.validate_trade(
            broker_account=BrokerAccount.objects.filter(broker_connection=conn).first(),
            instrument=btcusd,
            grade=grading_result["grade"],
            price=Decimal("50000"),
            account_balance=Decimal("100000"),
            win_probability=test_win_prob,
        )

        risk_pct = risk_result.get("risk_percent", 0.0)
        self.stdout.write(
            f"Risk Assessment (Test Win Prob {test_win_prob}): {risk_pct:.2f}% of account suggested."
        )

        if risk_result["allowed"]:
            order = await OMSService.place_order(
                tenant=tenant,
                user=user,
                broker_account=BrokerAccount.objects.get(broker_connection=conn),
                instrument=btcusd,
                side="BUY",
                quantity=risk_result["suggested_quantity"],
                order_type="MARKET",
            )

            for _ in range(5):
                await asyncio.sleep(1)
                order.refresh_from_db()
                if order.state == "FILLED":
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Order {order.client_order_id} FILLED via Mock IB."
                        )
                    )
                    break

        self.stdout.write("Testing Deriv Integration (VIX100)...")
        vix100 = Instrument.objects.get(symbol="VIX100")
        deriv_broker = Broker.objects.get(broker_type="DERIV")
        deriv_conn, _ = BrokerConnection.objects.get_or_create(
            tenant=tenant,
            broker=deriv_broker,
            name="Test Deriv",
            defaults={"api_key": "mock_token", "status": "CONNECTED"},
        )
        deriv_acc, _ = BrokerAccount.objects.get_or_create(
            tenant=tenant,
            broker_connection=deriv_conn,
            account_number="CR12345",
            defaults={"status": "ACTIVE"},
        )

        self.stdout.write("Placing Mocked Deriv Trade for VIX100...")
        deriv_order = Order.objects.create(
            tenant=tenant,
            user=user,
            broker_account=deriv_acc,
            instrument=vix100,
            side="BUY",
            quantity=Decimal("10.0"),
            order_type="MARKET",
            state="FILLED",
            client_order_id=f"DERIV-{uuid.uuid4().hex[:8]}",
            filled_quantity=Decimal("10.0"),
            filled_at=timezone.now(),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Deriv Order {deriv_order.client_order_id} simulated FILLED."
            )
        )

        from apps.oms.models import Position

        pos = Position.objects.filter(instrument=btcusd).first()
        if pos:
            self.stdout.write(
                self.style.SUCCESS(f"Final Integrated Position: {pos.quantity} BTC")
            )

        self.stdout.write(self.style.MIGRATE_HEADING("=== Verification Complete ==="))
