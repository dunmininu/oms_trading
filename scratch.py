import asyncio
import json

import websockets


async def fetch_deriv_symbols():
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"active_symbols": "brief", "product_type": "basic"}))
        res = await ws.recv()
        data = json.loads(res)

        # print some info
        symbols = data.get("active_symbols", [])
        for _s in symbols[:15]:
            pass

        volatilities = [s for s in symbols if "Volatility" in s["display_name"]]
        for _v in volatilities[:10]:
            pass


asyncio.run(fetch_deriv_symbols())
