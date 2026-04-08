from django.core.management.base import BaseCommand
from apps.brokers.models import Broker, BrokerConnection
from apps.tenants.models import Tenant
from django.conf import settings

class Command(BaseCommand):
    help = 'Seed initial broker data'

    def handle(self, *args, **options):
        tenant, created = Tenant.objects.update_or_create(
            slug='default',
            defaults={
                'name': 'Default Tenant',
                'subdomain': 'default',
                'display_name': 'Default Trading Tenant',
                'contact_email': 'admin@omstrading.com',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tenant: {tenant.name}'))

        broker, created = Broker.objects.update_or_create(
            name='INTERACTIVE_BROKERS',
            defaults={
                'display_name': 'Interactive Brokers',
                'broker_type': 'INTERACTIVE_BROKERS',
                'host': '127.0.0.1',
                'port': 7497,
                'is_active': True,
                'is_testing': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created broker: {broker.display_name}'))

        connection, created = BrokerConnection.objects.update_or_create(
            tenant=tenant,
            broker=broker,
            name='Main IB Connection',
            defaults={
                'status': 'DISCONNECTED',
                'host_override': '127.0.0.1',
                'port_override': 7497,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created connection: {connection.name}'))

        # 4. Create Deriv Broker
        deriv_broker, created = Broker.objects.update_or_create(
            name='DERIV',
            defaults={
                'display_name': 'Deriv (Binary.com)',
                'broker_type': 'DERIV',
                'host': 'wss://ws.binaryws.com/websockets/v3',
                'is_active': True,
                'is_testing': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created broker: {deriv_broker.display_name}'))

        # 5. Create VIX Instruments
        for vix_sym in ['VIX25', 'VIX100']:
            from apps.oms.models import Instrument
            Instrument.objects.update_or_create(
                symbol=vix_sym,
                defaults={
                    'name': f'Volatility {vix_sym} Index',
                    'instrument_type': 'OTHER',
                    'exchange': 'OTHER',
                    'is_active': True,
                    'is_tradable': True,
                }
            )
