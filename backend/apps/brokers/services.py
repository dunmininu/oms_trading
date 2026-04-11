import logging
<<<<<<< HEAD
from typing import Optional, Dict, Any
from django.utils import timezone
from django.conf import settings
from apps.brokers.models import Broker, BrokerConnection, BrokerAccount
from libs.ibsdk.client import IBClient
from libs.ibsdk.mock_client import MockIBClient
from libs.derivsdk.client import DerivClient

logger = logging.getLogger(__name__)

class BrokerService:
    _connections: Dict[str, Any] = {}

    @classmethod
    async def get_client(cls, connection_id: str) -> Any:
        if connection_id in cls._connections:
            return cls._connections[connection_id]

        try:
            conn = BrokerConnection.objects.select_related('broker').get(id=connection_id)

            if conn.broker.broker_type == 'DERIV':
                client = DerivClient(token=conn.api_key)
                cls._connections[connection_id] = client
                return client

            use_mock = (conn.host_override == '127.0.0.1' or not (conn.host_override or conn.broker.host))

            if use_mock:
                logger.info(f"Using MockIBClient for connection {connection_id}")
                client = MockIBClient(
                    host=conn.host_override or conn.broker.host,
                    port=conn.port_override or conn.broker.port,
                    client_id=1
=======
from typing import Any

from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.brokers.models import BrokerAccount, BrokerConnection
from libs.derivsdk.client import DerivClient
from libs.ibsdk.client import IBClient
from libs.ibsdk.mock_client import MockIBClient

logger = logging.getLogger(__name__)


class BrokerService:
    _connections: dict[str, Any] = {}

    @classmethod
    async def get_client(cls, connection_id: str) -> Any:
        import asyncio

        current_loop = asyncio.get_running_loop()

        # Connections dictionary now stores (client, loop_id)
        if connection_id in cls._connections:
            client, loop = cls._connections[connection_id]
            if loop == current_loop:
                return client
            else:
                logger.warning(
                    f"Loop mismatch for connection {connection_id}. Forcing fresh client."
                )
                # We don't delete the old one because another thread might still be using its loop
                # but we'll use a new one for THIS loop.

        @sync_to_async
        def _get_conn():
            return BrokerConnection.objects.select_related("broker").get(
                id=connection_id
            )

        try:
            conn = await _get_conn()

            if conn.broker.broker_type == "DERIV":
                client = DerivClient(token=conn.api_key)
                cls._connections[connection_id] = (client, current_loop)
                return client

            # Default logic for others
            use_mock = conn.host_override == "127.0.0.1" or not (
                conn.host_override or conn.broker.host
            )

            if use_mock:
                client = MockIBClient(
                    host=conn.host_override or conn.broker.host,
                    port=conn.port_override or conn.broker.port,
                    client_id=1,
>>>>>>> origin/main
                )
            else:
                client = IBClient(
                    host=conn.host_override or conn.broker.host,
                    port=conn.port_override or conn.broker.port,
<<<<<<< HEAD
                    client_id=1
                )

            cls._connections[connection_id] = client
=======
                    client_id=1,
                )

            cls._connections[connection_id] = (client, current_loop)
>>>>>>> origin/main
            return client
        except BrokerConnection.DoesNotExist:
            logger.error(f"BrokerConnection {connection_id} not found")
            raise

    @classmethod
    async def connect_broker(cls, connection_id: str) -> bool:
        try:
<<<<<<< HEAD
            conn = BrokerConnection.objects.get(id=connection_id)
            client = await cls.get_client(connection_id)
            if client.is_connected(): return True
            conn.status = 'CONNECTING'
            conn.save()
            success = await client.connect()
            if success:
                conn.status = 'CONNECTED'
                conn.last_connected = timezone.now()
                conn.save()
                await cls.sync_accounts(connection_id)
                return True
            else:
                conn.status = 'ERROR'
                conn.save()
                return False
=======

            @sync_to_async
            def _get_and_set_status(status):
                conn = BrokerConnection.objects.get(id=connection_id)
                conn.status = status
                conn.save()
                return conn

            client = await cls.get_client(connection_id)
            if client.is_connected:
                return True

            await _get_and_set_status("CONNECTING")
            success = await client.connect()

            @sync_to_async
            def _update_final_status(is_success):
                conn = BrokerConnection.objects.get(id=connection_id)
                if is_success:
                    conn.status = "CONNECTED"
                    conn.last_connected = timezone.now()
                else:
                    conn.status = "ERROR"
                conn.save()

            await _update_final_status(success)

            if success:
                await cls.sync_accounts(connection_id)
                return True
            return False
>>>>>>> origin/main
        except Exception as e:
            logger.exception(f"Error connecting broker {connection_id}: {e}")
            return False

    @classmethod
    async def sync_accounts(cls, connection_id: str):
        client = await cls.get_client(connection_id)
<<<<<<< HEAD
        if not client.is_connected(): return
        conn = BrokerConnection.objects.get(id=connection_id)
        ib_accounts = client.ib.managedAccounts()
        for acc_id in ib_accounts:
            BrokerAccount.objects.update_or_create(
                tenant=conn.tenant, broker_connection=conn, account_number=acc_id,
                defaults={'account_name': f"IB Account {acc_id}", 'status': 'ACTIVE'}
            )
=======
        # Ensure connection for Deriv
        if hasattr(client, "connect") and (
            not hasattr(client, "is_authenticated") or not client.is_authenticated
        ):
            logger.info(f"Initiating Deriv connection for sync: {connection_id}")
            connected = await client.connect()
            if not connected:
                logger.error(f"Failed to connect Deriv for sync: {connection_id}")
                return

        if (
            hasattr(client, "is_authenticated")
            and not client.is_authenticated
            or not hasattr(client, "is_authenticated")
            and hasattr(client, "is_connected")
            and not client.is_connected
        ):
            return

        @sync_to_async
        def _sync(managed_accounts):
            conn = BrokerConnection.objects.get(id=connection_id)
            for acc_id in managed_accounts:
                BrokerAccount.objects.update_or_create(
                    broker_connection=conn,
                    account_number=acc_id,
                    defaults={"account_name": f"Account {acc_id}", "status": "ACTIVE"},
                )

        # Pull accounts from client SDK
        if hasattr(client, "ib"):
            accounts = client.ib.managedAccounts()
        elif hasattr(client, "accounts"):  # Deriv path

            @sync_to_async
            def _sync_deriv(account_list, live_balances):
                logger.info(
                    f"Syncing {len(account_list)} Deriv accounts for connection {connection_id}"
                )
                try:
                    conn = BrokerConnection.objects.get(id=connection_id)
                except BrokerConnection.DoesNotExist:
                    logger.error(f"Connection {connection_id} not found during sync")
                    return

                for acc in account_list:
                    login_id = acc.get("loginid")
                    # Get True balance from get_balances payload or fallback to auth payload (which usually doesn't have it)
                    live_bal_info = live_balances.get(login_id, {})
                    true_balance = live_bal_info.get("balance", acc.get("balance", 0))

                    logger.info(
                        f"Registering account: {login_id} ({acc.get('account_type')} - Bal: {true_balance})"
                    )
                    BrokerAccount.objects.update_or_create(
                        broker_connection=conn,
                        account_number=login_id,
                        defaults={
                            "account_name": f"Deriv {acc.get('account_type', 'virtual').title()} ({login_id})",
                            "account_type": acc.get("account_type", "VIRTUAL").upper(),
                            "currency": acc.get("currency", "USD"),
                            "status": "ACTIVE"
                            if not acc.get("is_disabled")
                            else "INACTIVE",
                            "day_trading_buying_power": true_balance,
                        },
                    )
                logger.info("Deriv account sync complete")

            live_balances = await client.get_balances()
            await _sync_deriv(client.accounts, live_balances)
            return
        else:
            accounts = []

        await _sync(accounts)

    @classmethod
    async def sync_portfolio(cls, connection_id: str):
        """Sync open contracts from Deriv and update local Positions."""
        client = await cls.get_client(connection_id)
        if not hasattr(client, "get_portfolio"):
            return

        contracts = await client.get_portfolio()
        logger.info(f"Syncing {len(contracts)} open contracts from Deriv...")

        from decimal import Decimal

        from apps.oms.models import Instrument, Position

        @sync_to_async
        def _sync(contract_list):
            conn = BrokerConnection.objects.get(id=connection_id)
            main_account = BrokerAccount.objects.filter(
                broker_connection=conn, account_type__in=["VIRTUAL", "REAL"]
            ).first()
            if not main_account:
                return

            # Clear stale local positions for this account before re-syncing from source of truth
            # Actually, better to just update/create and leave others as 0?
            # Deriv Portfolio is ground truth.

            for c in contract_list:
                symbol = c.get("underlying_symbol")
                instrument = Instrument.objects.filter(symbol=symbol).first()
                if not instrument:
                    continue

                Position.objects.update_or_create(
                    broker_account=main_account,
                    instrument=instrument,
                    defaults={
                        "quantity": Decimal(str(c.get("buy_price", 0))),
                        "average_cost": Decimal(str(c.get("buy_price", 0))),
                        "market_price": Decimal(
                            str(c.get("bid_price", c.get("buy_price", 0)))
                        ),
                        "unrealized_pnl": Decimal(str(c.get("pnl", 0))),
                        "last_updated": timezone.now(),
                    },
                )

        await _sync(contracts)

    @classmethod
    async def sync_statement(cls, connection_id: str):
        """Sync historical transactions from Deriv and update local Orders."""
        client = await cls.get_client(connection_id)
        if not hasattr(client, "get_statement"):
            return

        transactions = await client.get_statement(limit=50)
        logger.info(
            f"Syncing {len(transactions)} historical transactions from Deriv..."
        )

        from decimal import Decimal

        from apps.oms.models import Instrument, Order

        @sync_to_async
        def _sync(tx_list):
            conn = BrokerConnection.objects.get(id=connection_id)
            main_account = BrokerAccount.objects.filter(
                broker_connection=conn, account_type__in=["VIRTUAL", "REAL"]
            ).first()
            if not main_account:
                return

            for tx in tx_list:
                # Map Deriv statement to Order
                if tx.get("action_type") not in ["buy", "sell"]:
                    continue

                contract_id = str(tx.get("contract_id"))
                longcode = tx.get("longcode", "")

                # Attempt to extract symbol from longcode (e.g. "Win payout if Volatility 100 Index...")
                symbol = None

                # Deriv common indices mapping helper
                if "Volatility 100" in longcode:
                    symbol = "R_100"
                elif "Volatility 75" in longcode:
                    symbol = "R_75"
                elif "Volatility 50" in longcode:
                    symbol = "R_50"
                elif "Volatility 25" in longcode:
                    symbol = "R_25"
                elif "Volatility 10" in longcode:
                    symbol = "R_10"

                instrument = None
                if symbol:
                    instrument = Instrument.objects.filter(symbol=symbol).first()

                if not instrument:
                    # Generic fallback to first active Deriv instrument if still unknown
                    instrument = Instrument.objects.filter(
                        exchange="DERIV", is_active=True
                    ).first()

                Order.objects.update_or_create(
                    broker_order_id=contract_id,
                    defaults={
                        "broker_account": main_account,
                        "instrument": instrument,
                        "client_order_id": f"SYNC-{tx.get('transaction_id')}",
                        "order_type": "MARKET",
                        "side": "BUY" if tx.get("action_type") == "buy" else "SELL",
                        "quantity": Decimal(str(tx.get("amount", 0))),
                        "state": "FILLED",
                        "submitted_at": timezone.datetime.fromtimestamp(
                            tx.get("transaction_time"), tz=timezone.utc
                        ),
                        "filled_at": timezone.datetime.fromtimestamp(
                            tx.get("transaction_time"), tz=timezone.utc
                        ),
                        "notes": longcode,
                    },
                )

        await _sync(transactions)
>>>>>>> origin/main

    @classmethod
    def disconnect_broker(cls, connection_id: str):
        if connection_id in cls._connections:
            cls._connections[connection_id].disconnect()
            conn = BrokerConnection.objects.get(id=connection_id)
<<<<<<< HEAD
            conn.status = 'DISCONNECTED'
=======
            conn.status = "DISCONNECTED"
>>>>>>> origin/main
            conn.last_disconnected = timezone.now()
            conn.save()
            del cls._connections[connection_id]
