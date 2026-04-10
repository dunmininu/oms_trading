"""
OMS services for order management, executions, positions, and P&L.
"""

import logging
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.brokers.models import BrokerAccount
from apps.brokers.services import BrokerService
from libs.ibsdk.contracts import create_btcusd_contract, create_gbpjpy_contract
from libs.ibsdk.orders import create_limit_order, create_market_order

from .models import Execution, Instrument, Order, Position

logger = logging.getLogger(__name__)


class OMSService:
    @classmethod
    async def place_order(
        cls,
        tenant,
        user,
        broker_account: BrokerAccount,
        instrument: Instrument,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        price: Decimal | None = None,
        strategy_run=None,
    ) -> Order:
        client_order_id = f"OMS-{uuid.uuid4().hex[:8]}"
        order = Order.objects.create(
            tenant=tenant,
            user=user,
            broker_account=broker_account,
            instrument=instrument,
            client_order_id=client_order_id,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            state="NEW",
            strategy_run=strategy_run,
        )

        try:
            connection_id = broker_account.broker_connection_id
            client = await BrokerService.get_client(connection_id)

            if not client.is_connected():
                await BrokerService.connect_broker(connection_id)
                if not client.is_connected():
                    order.state = "REJECTED"
                    order.reject_reason = "Broker disconnected"
                    order.save()
                    return order

            # Handle Deriv Trades
            if broker_account.broker_connection.broker.broker_type == "DERIV":
                order.state = "PENDING_SUBMIT"
                order.save()

                # Deriv typically uses 'CALL' for Buy and 'PUT' for Sell in digital options
                # Or regular trades if using their MT5/Binary API
                contract_type = "CALL" if side == "BUY" else "PUT"
                response = await client.place_trade(
                    instrument.symbol, float(quantity), contract_type
                )

                if "error" in response:
                    order.state = "REJECTED"
                    order.reject_reason = response["error"]["message"]
                    order.save()
                    return order

                order.broker_order_id = str(response["buy"]["contract_id"])
                order.state = "FILLED"  # Deriv digital options are immediate
                order.filled_quantity = quantity
                order.filled_at = timezone.now()
                order.save()

                # Update position for Deriv
                cls._update_deriv_position(order, response)
                return order

            # Handle IB Trades
            if instrument.symbol == "GBPJPY":
                contract = create_gbpjpy_contract()
            elif instrument.symbol == "BTCUSD" or instrument.symbol == "BTC":
                contract = create_btcusd_contract()
            else:
                from ib_insync import Stock

                contract = Stock(
                    instrument.symbol,
                    instrument.exchange or "SMART",
                    instrument.currency or "USD",
                )

            await client.get_contract_details(contract)

            if order_type == "MARKET":
                ib_order = create_market_order(side, float(quantity))
            elif order_type == "LIMIT":
                ib_order = create_limit_order(side, float(quantity), float(price))
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            order.state = "PENDING_SUBMIT"
            order.save()

            trade = client.place_order(contract, ib_order)

            order.broker_order_id = str(trade.order.orderId)
            order.state = "SUBMITTED"
            order.submitted_at = timezone.now()
            order.save()

            trade.statusEvent += lambda t: cls._handle_ib_status_update(order.id, t)
            trade.fillEvent += lambda t, f: cls._handle_ib_fill(order.id, t, f)

            return order

        except Exception as e:
            logger.exception(f"Failed to place order {client_order_id}: {e}")
            order.state = "REJECTED"
            order.reject_reason = str(e)
            order.save()
            return order

    @classmethod
    def _handle_ib_status_update(cls, order_id, trade):
        try:
            order = Order.objects.get(id=order_id)
            status_map = {
                "Submitted": "SUBMITTED",
                "Filled": "FILLED",
                "Cancelled": "CANCELLED",
                "Inactive": "REJECTED",
                "PendingSubmit": "PENDING_SUBMIT",
                "PreSubmitted": "SUBMITTED",
            }
            new_state = status_map.get(trade.orderStatus.status, order.state)
            if order.state != new_state:
                order.state = new_state
                if new_state == "FILLED":
                    order.filled_at = timezone.now()
                order.save()
        except Exception:
            pass

    @classmethod
    def _handle_ib_fill(cls, order_id, trade, fill):
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)

                # Create Execution record
                Execution.objects.create(
                    tenant=order.tenant,
                    order=order,
                    execution_id=fill.execution.execId,
                    broker_execution_id=fill.execution.execId,
                    quantity=Decimal(str(fill.execution.shares)),
                    price=Decimal(str(fill.execution.price)),
                    commission=Decimal(
                        str(
                            fill.commissionReport.commission
                            if fill.commissionReport
                            else 0
                        )
                    ),
                    currency=fill.contract.currency,
                    executed_at=timezone.now(),
                )

                # Update Order filled quantity
                order.filled_quantity += Decimal(str(fill.execution.shares))
                if order.filled_quantity >= order.quantity:
                    order.state = "FILLED"
                    order.filled_at = timezone.now()
                else:
                    order.state = "PARTIALLY_FILLED"
                order.save()

                # Update Position
                cls._update_position(order, fill)

        except Exception:
            pass

    @classmethod
    def _update_deriv_position(cls, order, response):
        """Update position for Deriv trades."""
        pos, created = Position.objects.get_or_create(
            tenant=order.tenant,
            broker_account=order.broker_account,
            instrument=order.instrument,
            defaults={"quantity": Decimal("0.0000"), "average_cost": Decimal("0.0000")},
        )

        buy_price = Decimal(str(response["buy"]["price"]))
        if order.side == "BUY":
            pos.quantity += order.quantity
            pos.average_cost = buy_price
        else:
            pos.quantity -= order.quantity

        pos.save()

    @classmethod
    def _update_position(cls, order, fill):
        pos, created = Position.objects.get_or_create(
            tenant=order.tenant,
            broker_account=order.broker_account,
            instrument=order.instrument,
            defaults={"quantity": Decimal("0.0000"), "average_cost": Decimal("0.0000")},
        )

        fill_qty = Decimal(str(fill.execution.shares))
        fill_price = Decimal(str(fill.execution.price))

        if order.side in ["BUY", "BUY_TO_COVER"]:
            new_qty = pos.quantity + fill_qty
            if new_qty != 0:
                pos.average_cost = (
                    (pos.quantity * (pos.average_cost or 0)) + (fill_qty * fill_price)
                ) / new_qty
            pos.quantity = new_qty
        else:  # SELL or SELL_SHORT
            new_qty = pos.quantity - fill_qty
            pos.quantity = new_qty

        pos.save()


class OrderService:
    def __init__(self, tenant=None, user=None):
        self.tenant = tenant
        self.user = user


class ExecutionService:
    def __init__(self, tenant=None, user=None):
        self.tenant = tenant
        self.user = user


class PositionService:
    def __init__(self, tenant=None, user=None):
        self.tenant = tenant
        self.user = user


class PnLService:
    def __init__(self, tenant=None, user=None):
        self.tenant = tenant
        self.user = user
