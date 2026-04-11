"""
Autonomous Execution Engine for live trading on Deriv.
"""

import logging
from decimal import Decimal
from typing import Any

from asgiref.sync import async_to_sync
from django.utils import timezone

from apps.brokers.models import BrokerAccount, BrokerConnection
from apps.brokers.services import BrokerService
from apps.oms.models import Instrument

from .risk_services import RiskManagementService

logger = logging.getLogger(__name__)


class AutonomousExecutionService:
    """Service to bridge identified signals into live executed orders."""

    @classmethod
    def execute_signal(cls, instrument: Instrument, signal_data: dict[str, Any]):
        """
        Evaluate and execute a signal on the best available broker connection.
        """
        grade = signal_data.get("grade", "D-")
        direction = signal_data.get("direction", "NONE")

        if direction == "NONE":
            return {"status": "skipped", "reason": "No clear direction"}

        # 1. Identify live connection (Prefer Deriv for synthetics)
        try:
            conn = BrokerConnection.objects.filter(
                broker__broker_type="DERIV", broker__is_active=True
            ).first()

            if not conn:
                logger.warning(
                    f"Execution skipped for {instrument.symbol}: No active Deriv broker configuration found."
                )
                return {"status": "error", "reason": "No connected broker"}

            # 2. Get Account from System Settings
            from apps.core.models import SystemConfiguration

            active_account_id = SystemConfiguration.get_value("ACTIVE_TRADING_ACCOUNT")

            if not active_account_id:
                logger.warning(
                    "Execution skipped: No active trading account locked in settings."
                )
                return {
                    "status": "blocked",
                    "reason": "No active trading account selected",
                }

            account = BrokerAccount.objects.filter(
                broker_connection=conn, account_number=active_account_id
            ).first()
            if not account:
                return {
                    "status": "error",
                    "reason": f"Selected trading account {active_account_id} not found under active broker.",
                }

            # 3. Dynamic Real-Time Balance Verification
            # We strictly fetch from the WebSocket to ensure atomic precision for risk-sizing
            try:
                live_bal = cls._fetch_live_balance(conn.id, active_account_id)
                if live_bal is not None:
                    balance = Decimal(str(live_bal))
                    # Opportunistic DB sync for the dashboard
                    if account.day_trading_buying_power != balance:
                        account.day_trading_buying_power = balance
                        account.save(update_fields=["day_trading_buying_power"])
                else:
                    balance = (
                        account.day_trading_buying_power
                        if account.day_trading_buying_power
                        else Decimal("0.00")
                    )
            except Exception as e:
                logger.error(f"Live balance fetch failed, falling back to db: {e}")
                balance = (
                    account.day_trading_buying_power
                    if account.day_trading_buying_power
                    else Decimal("0.00")
                )

            if balance <= 0:
                return {"status": "blocked", "reason": "Account balance is zero/empty"}

            risk_check = RiskManagementService.validate_trade(
                account,
                instrument,
                grade,
                instrument.last_price or Decimal("1000"),
                balance,
            )

            if not risk_check["allowed"]:
                logger.info(
                    f"Execution BLOCKED for {instrument.symbol} by Risk Guard: {risk_check['reason']}"
                )
                return {"status": "blocked", "reason": risk_check["reason"]}

            # 4. Dispatch Order (Async/Dynamic)
            cls._place_deriv_order(
                conn, account, instrument, direction, risk_check, signal_data
            )

            return {
                "status": "success",
                "message": f"Order dispatched for {instrument.symbol}",
            }

        except Exception as e:
            logger.exception(f"Execution Engine Failure: {e}")
            return {"status": "error", "reason": str(e)}

    @classmethod
    @async_to_sync
    async def _fetch_live_balance(cls, conn_id: str, account_id: str) -> float | None:
        """Atomically fetch the live balance via websocket before trade sizing."""
        client = await BrokerService.get_client(conn_id)
        if hasattr(client, "is_connected") and not client.is_connected:
            await client.connect()
        elif not hasattr(client, "is_connected"):
            await BrokerService.connect_broker(conn_id)

        if hasattr(client, "get_balances"):
            balances = await client.get_balances()
            return balances.get(account_id, {}).get("balance")
        return None

    @classmethod
    @async_to_sync
    async def _place_deriv_order(
        cls, conn, account, instrument, direction, risk, signal_data
    ):
        """Place Multiplier order on Deriv via WebSocket SDK."""
        client = await BrokerService.get_client(conn.id)

        # Ensure connection is actually awake
        if hasattr(client, "is_connected") and not client.is_connected:
            connected = await client.connect()
            if not connected:
                logger.error(
                    f"Failed to wake up Deriv connection for order execution: {conn.id}"
                )
                return
        elif not hasattr(client, "is_connected"):
            # Fallback if property is missing but connect() requires calling
            await BrokerService.connect_broker(conn.id)

        # Mapping direction to contract type
        # For Multipliers, we use 'MULTUP' or 'MULTDOWN'
        contract_type = "MULTUP" if direction == "LONG" else "MULTDOWN"

        # Stake calculation (1% default if not specified)
        stake = float(risk.get("max_risk_amount", 10))

        # Use signal-calculated SL/TP if available, otherwise fallback to heuristics
        sl_price = signal_data.get("sl_price")
        tp_price = signal_data.get("tp_price")

        limit_order = {}
        if sl_price:
            limit_order["stop_loss"] = float(sl_price)
        else:
            limit_order["stop_loss"] = float(stake * 0.5)  # Heuristic fallback

        if tp_price:
            limit_order["take_profit"] = float(tp_price)
        else:
            limit_order["take_profit"] = float(stake * 1.5)

        try:
            # We use multipliers for ICT setups to support SL/TP effectively
            request = {
                "buy": 1,
                "price": stake,
                "parameters": {
                    "amount": stake,
                    "basis": "stake",
                    "contract_type": contract_type,
                    "currency": "USD",
                    "symbol": instrument.symbol,
                    "multiplier": 100,  # Strategy default
                    "limit_order": limit_order,
                },
            }

            logger.info(
                f"Deriv Execution Request: {instrument.symbol} {contract_type} @ Stake {stake}"
            )

            import json

            await client.ws.send(json.dumps(request))
            response = await client.ws.recv()
            data = json.loads(response)

            if "error" in data:
                logger.error(f"Deriv Trade ERROR: {data['error']['message']}")
                # Record the rejection in DB if possible
                from asgiref.sync import sync_to_async
                from django.utils.crypto import get_random_string

                from apps.oms.models import Order

                @sync_to_async
                def _log_rejection():
                    Order.objects.create(
                        broker_account=account,
                        instrument=instrument,
                        client_order_id=f"REJ-{get_random_string(8)}",
                        order_type="MARKET",
                        side="BUY" if direction == "LONG" else "SELL",
                        quantity=Decimal(str(stake)),
                        state="REJECTED",
                        reject_reason=data["error"]["message"],
                        submitted_at=timezone.now(),
                    )

                await _log_rejection()
                return

            # Log Successful Order in OMS
            from asgiref.sync import sync_to_async
            from django.utils.crypto import get_random_string

            from apps.oms.models import Order

            @sync_to_async
            def _create_db_order():
                logger.info(f"Persisting Order to DB: {data['buy']['contract_id']}")
                return Order.objects.create(
                    broker_account=account,
                    instrument=instrument,
                    client_order_id=f"AUTON-{get_random_string(8)}",
                    broker_order_id=str(data["buy"]["contract_id"]),
                    order_type="MARKET",
                    side="BUY" if direction == "LONG" else "SELL",
                    quantity=Decimal(str(stake)),
                    state="FILLED",
                    submitted_at=timezone.now(),
                    filled_at=timezone.now(),
                )

            order = await _create_db_order()
            logger.info(
                f"Live Trade Synchronized: {instrument.symbol} {direction} (Order ID: {order.id})"
            )

        except Exception as e:
            logger.exception(f"Failed to transmit live order: {e}")
