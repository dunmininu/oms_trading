"""
Integrated Verification strategy that tests ICT detection, Grading, and Risk management.
"""

import asyncio
import logging
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.brokers.services import BrokerService
from apps.brokers.models import BrokerConnection, BrokerAccount
from apps.oms.services import OMSService
from apps.marketdata.services import MarketDataService
from apps.strategies.ict_services import ICTSetupService
from apps.strategies.quant_services import QuantService
from apps.strategies.grading_services import GradingService
from apps.strategies.risk_services import RiskManagementService
from apps.tenants.models import Tenant
from apps.core.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run full integrated verification strategy'

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        asyncio.run(self.run_verification())

    async def run_verification(self):
        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting Full Integrated Verification ---"))

        # 1. Setup Environment
        tenant = Tenant.objects.get(slug='default')
        user = User.objects.get(email='admin@omstrading.com')
        conn = BrokerConnection.objects.get(tenant=tenant, name='Main IB Connection')

        # 2. Ensure instruments exist and fetch data
        gbpjpy, btcusd = await MarketDataService.ensure_instruments()
        client = await BrokerService.get_client(conn.id)
        await BrokerService.connect_broker(conn.id)

        self.stdout.write("Fetching historical data for BTCUSD...")
        await MarketDataService.fetch_historical_ohlcv(client, btcusd, duration='2 D', bar_size='15 mins')
        await MarketDataService.fetch_historical_ohlcv(client, btcusd, duration='5 D', bar_size='4 hours')

        # 3. Test Detection & Grading
        self.stdout.write("Running Strategy Detection & Grading...")
        grading_result = GradingService.grade_setup(btcusd, '15_MINUTE')
        self.stdout.write(f"Setup Grade: {grading_result['grade']} (Score: {grading_result['score']})")
        self.stdout.write(f"Direction: {grading_result['direction']}, Signals: {grading_result['ict_signals']}")

        # 4. Test Risk Validation
        self.stdout.write("Running Risk Validation...")
        # Assume $100k balance for testing
        risk_result = RiskManagementService.validate_trade(
            broker_account=BrokerAccount.objects.get(broker_connection=conn),
            instrument=btcusd,
            grade=grading_result['grade'],
            price=Decimal('50000'),
            account_balance=Decimal('100000')
        )

        if risk_result['allowed']:
            self.stdout.write(self.style.SUCCESS(f"Trade ALLOWED. Suggested Qty: {risk_result['suggested_quantity']}"))

            # 5. Place the trade
            self.stdout.write("Placing Order...")
            order = await OMSService.place_order(
                tenant=tenant,
                user=user,
                broker_account=BrokerAccount.objects.get(broker_connection=conn),
                instrument=btcusd,
                side='BUY' if grading_result['direction'] == 'LONG' else 'SELL',
                quantity=risk_result['suggested_quantity'],
                order_type='MARKET'
            )

            # 6. Wait for fill
            self.stdout.write("Waiting for order fill...")
            for _ in range(10):
                await asyncio.sleep(1)
                order.refresh_from_db()
                if order.state == 'FILLED':
                    self.stdout.write(self.style.SUCCESS(f"Order FILLED! Executed at: {order.filled_at}"))
                    break
        else:
            self.stdout.write(self.style.WARNING(f"Trade BLOCKED: {risk_result['reason']}"))

        # 7. Final Position Check
        from apps.oms.models import Position
        pos = Position.objects.filter(instrument=btcusd).first()
        if pos:
            self.stdout.write(f"Final Position: {pos.quantity} BTC @ {pos.average_cost}")

        BrokerService.disconnect_broker(conn.id)
        self.stdout.write(self.style.MIGRATE_HEADING("--- Verification Complete ---"))
