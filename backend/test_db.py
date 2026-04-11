import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


from apps.brokers.models import BrokerAccount, BrokerConnection  # noqa: E402

for _conn in BrokerConnection.objects.all():
    pass

for acc in BrokerAccount.objects.all():
    if acc.metadata:
        pass
