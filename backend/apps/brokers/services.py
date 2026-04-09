import logging
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
                )
            else:
                client = IBClient(
                    host=conn.host_override or conn.broker.host,
                    port=conn.port_override or conn.broker.port,
                    client_id=1
                )

            cls._connections[connection_id] = client
            return client
        except BrokerConnection.DoesNotExist:
            logger.error(f"BrokerConnection {connection_id} not found")
            raise

    @classmethod
    async def connect_broker(cls, connection_id: str) -> bool:
        try:
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
        except Exception as e:
            logger.exception(f"Error connecting broker {connection_id}: {e}")
            return False

    @classmethod
    async def sync_accounts(cls, connection_id: str):
        client = await cls.get_client(connection_id)
        if not client.is_connected(): return
        conn = BrokerConnection.objects.get(id=connection_id)
        ib_accounts = client.ib.managedAccounts()
        for acc_id in ib_accounts:
            BrokerAccount.objects.update_or_create(
                tenant=conn.tenant, broker_connection=conn, account_number=acc_id,
                defaults={'account_name': f"IB Account {acc_id}", 'status': 'ACTIVE'}
            )

    @classmethod
    def disconnect_broker(cls, connection_id: str):
        if connection_id in cls._connections:
            cls._connections[connection_id].disconnect()
            conn = BrokerConnection.objects.get(id=connection_id)
            conn.status = 'DISCONNECTED'
            conn.last_disconnected = timezone.now()
            conn.save()
            del cls._connections[connection_id]
