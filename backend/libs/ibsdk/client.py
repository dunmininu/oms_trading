"""
Enhanced Interactive Brokers client using ib_insync.
"""

import logging
from typing import Any

import eventkit as ek
from ib_insync import IB, Contract, Fill, Order, Ticker

logger = logging.getLogger(__name__)


class IBClient:
    """
    Enhanced IB client with improved connection management and event handling.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self._reconnect_delay = 5
        self._max_reconnect_attempts = 5

        # Events
        self.connected_event = ek.Event()
        self.disconnected_event = ek.Event()
        self.error_event = ek.Event()
        self.order_status_event = ek.Event()
        self.exec_details_event = ek.Event()
        self.pending_tickers_event = ek.Event()

        # Setup ib_insync callbacks
        self.ib.connectedEvent += self._on_connected
        self.ib.disconnectedEvent += self._on_disconnected
        self.ib.errorEvent += self._on_error
        self.ib.orderStatusEvent += self._on_order_status
        self.ib.execDetailsEvent += self._on_exec_details
        self.ib.pendingTickersEvent += self._on_pending_tickers

    async def connect(self) -> bool:
        """Connect to IB Gateway/TWS."""
        try:
            logger.info(
                f"Connecting to IB at {self.host}:{self.port} with client_id {self.client_id}"
            )
            await self.ib.connectAsync(self.host, self.port, self.client_id)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IB: {e}")
            self.error_event.emit(None, None, str(e))
            return False

    def disconnect(self):
        """Disconnect from IB Gateway/TWS."""
        if self.ib.isConnected():
            self.ib.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to IB."""
        return self.ib.isConnected()

    # Callback handlers
    def _on_connected(self):
        logger.info("Connected to IB")
        self.connected_event.emit()

    def _on_disconnected(self):
        logger.warning("Disconnected from IB")
        self.disconnected_event.emit()

    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract: Any):
        logger.error(f"IB Error {errorCode}: {errorString} (reqId: {reqId})")
        self.error_event.emit(reqId, errorCode, errorString)

    def _on_order_status(self, trade: Any):
        logger.info(f"Order Status Update: {trade.orderStatus.status}")
        self.order_status_event.emit(trade)

    def _on_exec_details(self, trade: Any, fill: Fill):
        logger.info(f"Execution Details: {fill.execution.execId}")
        self.exec_details_event.emit(trade, fill)

    def _on_pending_tickers(self, tickers: list[Ticker]):
        self.pending_tickers_event.emit(tickers)

    # Utilities
    async def get_contract_details(self, contract: Contract):
        """Fetch contract details."""
        return await self.ib.qualifyContractsAsync(contract)

    def place_order(self, contract: Contract, order: Order):
        """Place an order."""
        return self.ib.placeOrder(contract, order)

    def cancel_order(self, order: Order):
        """Cancel an order."""
        return self.ib.cancelOrder(order)

    async def req_historical_data(
        self,
        contract: Contract,
        endDateTime: str,
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: bool,
    ):
        """Request historical data."""
        return await self.ib.reqHistoricalDataAsync(
            contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH
        )

    def req_mkt_data(
        self,
        contract: Contract,
        genericTickList: str = "",
        snapshot: bool = False,
        regulatorySnapshot: bool = False,
    ):
        """Request real-time market data."""
        return self.ib.reqMktData(
            contract, genericTickList, snapshot, regulatorySnapshot
        )
