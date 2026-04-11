"""
Verification strategy to test paper trading.
"""

import asyncio
import logging
import os
from decimal import Decimal
<<<<<<< HEAD
from django.core.management.base import BaseCommand
from apps.brokers.services import BrokerService
from apps.brokers.models import BrokerConnection, BrokerAccount
from apps.oms.services import OMSService
from apps.marketdata.services import MarketDataService
from apps.tenants.models import Tenant
from apps.core.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run verification strategy for paper trading'
=======

from django.core.management.base import BaseCommand

from apps.brokers.models import BrokerAccount, BrokerConnection
from apps.brokers.services import BrokerService
from apps.core.models import User
from apps.marketdata.services import MarketDataService
from apps.oms.services import OMSService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run verification strategy for paper trading"
>>>>>>> origin/main

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        asyncio.run(self.run_verification())

    async def run_verification(self):
        self.stdout.write("Starting Paper Trade Verification...")
<<<<<<< HEAD

        # 1. Setup Environment
        tenant = Tenant.objects.get(slug='default')
        user = User.objects.get(email='admin@omstrading.com')
        conn = BrokerConnection.objects.get(tenant=tenant, name='Main IB Connection')

        # 2. Ensure instruments exist
        gbpjpy, btcusd = await MarketDataService.ensure_instruments()

=======

        # 1. Setup Environment
        # 1. Setup Environment
        user = User.objects.get(email="admin@omstrading.com")
        conn = BrokerConnection.objects.get(name="Main IB Connection")

        # 2. Ensure instruments exist
        gbpjpy, btcusd = await MarketDataService.ensure_instruments()

>>>>>>> origin/main
        # 3. Connect Broker
        success = await BrokerService.connect_broker(conn.id)
        if not success:
            self.stdout.write(self.style.ERROR("Failed to connect to IB Gateway"))
            return

        # 4. Get Account
        account = BrokerAccount.objects.filter(broker_connection=conn).first()
        if not account:
<<<<<<< HEAD
            self.stdout.write(self.style.ERROR("No broker account found after connection"))
=======
            self.stdout.write(
                self.style.ERROR("No broker account found after connection")
            )
>>>>>>> origin/main
            return

        self.stdout.write(f"Using account: {account.account_number}")

        # 5. Place a small test order (0.001 BTC)
<<<<<<< HEAD
        self.stdout.write(f"Placing Market BUY order for 0.001 BTCUSD...")
        order = await OMSService.place_order(
            tenant=tenant,
            user=user,
            broker_account=account,
            instrument=btcusd,
            side='BUY',
            quantity=Decimal('0.001'),
            order_type='MARKET'
        )

        self.stdout.write(f"Order created: {order.client_order_id}, State: {order.state}")

=======
        self.stdout.write("Placing Market BUY order for 0.001 BTCUSD...")
        order = await OMSService.place_order(
            user=user,
            broker_account=account,
            instrument=btcusd,
            side="BUY",
            quantity=Decimal("0.001"),
            order_type="MARKET",
        )

        self.stdout.write(
            f"Order created: {order.client_order_id}, State: {order.state}"
        )

>>>>>>> origin/main
        # 6. Wait for fill (Wait up to 30 seconds)
        self.stdout.write("Waiting for order fill...")
        for _ in range(30):
            await asyncio.sleep(1)
            order.refresh_from_db()
<<<<<<< HEAD
            if order.state == 'FILLED':
                self.stdout.write(self.style.SUCCESS(f"Order FILLED! Executed at: {order.filled_at}"))
                break
            elif order.state == 'REJECTED':
                self.stdout.write(self.style.ERROR(f"Order REJECTED: {order.reject_reason}"))
                break
        else:
            self.stdout.write(self.style.WARNING(f"Order timed out. Current state: {order.state}"))

        # 7. Check Position
        from apps.oms.models import Position
        pos = Position.objects.filter(broker_account=account, instrument=btcusd).first()
        if pos:
            self.stdout.write(f"Current Position: {pos.quantity} BTC @ {pos.average_cost}")
=======
            if order.state == "FILLED":
                self.stdout.write(
                    self.style.SUCCESS(f"Order FILLED! Executed at: {order.filled_at}")
                )
                break
            elif order.state == "REJECTED":
                self.stdout.write(
                    self.style.ERROR(f"Order REJECTED: {order.reject_reason}")
                )
                break
        else:
            self.stdout.write(
                self.style.WARNING(f"Order timed out. Current state: {order.state}")
            )

        # 7. Check Position
        from apps.oms.models import Position

        pos = Position.objects.filter(broker_account=account, instrument=btcusd).first()
        if pos:
            self.stdout.write(
                f"Current Position: {pos.quantity} BTC @ {pos.average_cost}"
            )
>>>>>>> origin/main

        # 8. Clean up
        BrokerService.disconnect_broker(conn.id)
        self.stdout.write("Verification complete.")
