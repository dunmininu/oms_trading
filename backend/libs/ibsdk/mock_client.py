"""
Mock Interactive Brokers client for development and testing.
"""

import asyncio
import logging
import random
import uuid

import eventkit as ek
from ib_insync import (
    CommissionReport,
    Contract,
    Fill,
    Order,
)
from ib_insync import (
    Execution as IBExecution,
)

logger = logging.getLogger(__name__)


class MockTrade:
    def __init__(self, contract, order):
        self.contract = contract
        self.order = order
        self.orderStatus = type("Status", (), {"status": "Submitted"})()
        self.fills = []
        self.statusEvent = ek.Event()
        self.fillEvent = ek.Event()


class MockIB:
    def __init__(self):
        self.connected = False

    def isConnected(self):
        return self.connected

    def connect(self, *args, **kwargs):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def managedAccounts(self):
        return ["MOCK12345"]


class MockIBClient:
    """
    Mock IB client that simulates connectivity and order execution.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = MockIB()

        # Events
        self.connected_event = ek.Event()
        self.disconnected_event = ek.Event()
        self.error_event = ek.Event()
        self.order_status_event = ek.Event()
        self.exec_details_event = ek.Event()
        self.pending_tickers_event = ek.Event()

    async def connect(self) -> bool:
        await asyncio.sleep(0.1)
        self.ib.connect()
        logger.info(f"MOCK: Connected to IB at {self.host}:{self.port}")
        self.connected_event.emit()
        return True

    def disconnect(self):
        self.ib.disconnect()
        self.disconnected_event.emit()

    def is_connected(self) -> bool:
        return self.ib.isConnected()

    async def get_contract_details(self, contract: Contract):
        contract.conId = random.randint(1000, 9999)
        return [contract]

    def place_order(self, contract: Contract, order: Order):
        print(
            f"MOCK: Placing order {order.action} {order.totalQuantity} {contract.symbol}"
        )

        order.orderId = random.randint(10000, 99999)
        trade = MockTrade(contract, order)

        # Simulate fill in background
        asyncio.create_task(self._simulate_fill(trade))

        return trade

    async def _simulate_fill(self, trade):
        try:
            await asyncio.sleep(0.5)
            print(f"MOCK: Simulating fill for {trade.contract.symbol}")

            trade.orderStatus.status = "Filled"

            fill = Fill(
                contract=trade.contract,
                execution=IBExecution(
                    execId=f"exec-{uuid.uuid4().hex[:8]}",
                    shares=trade.order.totalQuantity,
                    price=50000.0 if trade.contract.symbol == "BTC" else 180.0,
                    avgPrice=50000.0 if trade.contract.symbol == "BTC" else 180.0,
                ),
                commissionReport=CommissionReport(commission=1.0),
                time=None,
            )

            trade.fills.append(fill)
            print("MOCK: Emitting fill events")
            trade.fillEvent.emit(trade, fill)
            trade.statusEvent.emit(trade)
            self.order_status_event.emit(trade)
            self.exec_details_event.emit(trade, fill)
            print("MOCK: Fill events emitted")
        except Exception as e:
            print(f"MOCK ERROR in _simulate_fill: {e}")

    def cancel_order(self, order: Order):
        pass

    async def req_historical_data(
        self, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH
    ):
        from datetime import datetime, timedelta

        from ib_insync import BarData

        bars = []
        now = datetime.now()
        base_price = 50000.0 if contract.symbol == "BTC" else 180.0
        for i in range(100):
            bars.append(
                BarData(
                    date=now - timedelta(minutes=15 * (100 - i)),
                    open=base_price + random.uniform(-10, 10),
                    high=base_price + random.uniform(10, 20),
                    low=base_price + random.uniform(-20, -10),
                    close=base_price + random.uniform(-5, 5),
                    volume=100,
                    average=base_price,
                    barCount=10,
                )
            )
        return bars

    def req_mkt_data(
        self, contract, genericTickList="", snapshot=False, regulatorySnapshot=False
    ):
        return None
