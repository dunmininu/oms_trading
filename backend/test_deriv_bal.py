import asyncio
import json
import os

# The user's token is in the DB. Let's fetch it from DB.
import django
import websockets

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from apps.brokers.models import BrokerConnection  # noqa: E402


async def check():
    conn = BrokerConnection.objects.filter(broker__name="DERIV").first()
    if not conn:
        return
    token = conn.api_key
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"authorize": token}))
        auth_res = json.loads(await ws.recv())
        if "error" in auth_res:
            return

        await ws.send(json.dumps({"balance": 1, "account": "all"}))
        json.loads(await ws.recv())


asyncio.run(check())
