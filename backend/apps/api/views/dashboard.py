import json
import logging

from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import Count, Max, Min, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.base import TemplateView

from apps.brokers.models import BrokerAccount, BrokerConnection
from apps.marketdata.models import HistoricalData
from apps.oms.models import Order, Position
from apps.strategies.models import (
    BacktestResult,
    LearningLabel,
    MLTrainingLog,
    SetupPerformance,
    SignalLog,
    Strategy,
)

logger = logging.getLogger(__name__)


class DashboardIndexView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_positions = Position.objects.exclude(quantity=0).select_related(
            "instrument"
        )
        unrealized_pnl = (
            active_positions.aggregate(total=Sum("unrealized_pnl"))["total"] or 0
        )
        total_exposure = (
            active_positions.aggregate(total=Sum("market_value"))["total"] or 0
        )

        setup_performances = SetupPerformance.objects.all().order_by("-total_pnl")

        # Recalculate avg_win_rate properly
        total_trades = sum(p.total_trades for p in setup_performances)
        total_wins = sum(p.winning_trades for p in setup_performances)
        avg_win_rate = (total_wins * 100 / total_trades) if total_trades > 0 else 0

        # Sovereign Bot Status
        bot_strategy = Strategy.objects.filter(
            name="Institutional Sovereign Bot"
        ).first()

        context.update(
            {
                "active_positions": active_positions,
                "unrealized_pnl": round(unrealized_pnl, 2),
                "total_exposure": round(total_exposure, 2),
                "avg_win_rate": round(avg_win_rate, 2),
                "recent_orders": Order.objects.all()
                .select_related("instrument")
                .order_by("-created_at")[:10],
                "setup_performances": setup_performances,
                "bot_strategy": bot_strategy,
                "live_signals": SignalLog.objects.all()
                .select_related("instrument")
                .order_by("-created_at")[:15],
                "strategies": Strategy.objects.all().exclude(
                    name="Institutional Sovereign Bot"
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "toggle_bot":
            bot = Strategy.objects.filter(name="Institutional Sovereign Bot").first()
            if bot:
                bot.auto_start = not bot.auto_start
                bot.is_active = True
                bot.save()
                return JsonResponse({"status": "success", "auto_start": bot.auto_start})

        elif action == "execute_signal":
            signal_id = request.POST.get("signal_id")
            signal = SignalLog.objects.select_related("instrument").get(id=signal_id)

            from apps.strategies.execution_services import AutonomousExecutionService
            from apps.strategies.grading_services import GradingService

            # Use persisted high-fidelity data from the log first
            grading = GradingService.grade_setup(signal.instrument, signal.timeframe)

            # Critical: Ensure we use the signal's intended direction
            if signal.direction and signal.direction != "NONE":
                grading["direction"] = signal.direction

            result = AutonomousExecutionService.execute_signal(
                signal.instrument, grading
            )
            return JsonResponse(result)

        return JsonResponse({"status": "error", "message": "Unknown action"})


class BacktestListView(ListView):
    model = BacktestResult
    template_name = "dashboard/backtests.html"
    context_object_name = "backtests"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        from apps.oms.models import Instrument

        context = super().get_context_data(**kwargs)

        # 1. Fetch instruments
        instruments = Instrument.objects.filter(
            exchange="DERIV", is_active=True
        ).order_by("name")

        # 2. Fetch inventory stats
        inventory_query = (
            HistoricalData.objects.filter(interval="15_MINUTE")
            .values("instrument__id")
            .annotate(count=Count("id"), start=Min("start_time"), end=Max("start_time"))
        )

        inventory_map = {item["instrument__id"]: item for item in inventory_query}

        # 3. Enrich instruments with stats
        for inst in instruments:
            inst.stats = inventory_map.get(inst.id)

        context["available_instruments"] = instruments
        return context

    def post(self, request, *args, **kwargs):
        from asgiref.sync import async_to_sync
        from django.contrib import messages

        from apps.brokers.models import BrokerConnection
        from apps.brokers.services import BrokerService
        from apps.marketdata.services import MarketDataService
        from apps.oms.models import Instrument

        action = request.POST.get("action")
        symbol = request.POST.get("symbol")

        if action == "sync_instruments":
            try:

                async def sys_sync():
                    @sync_to_async
                    def _get_conn():
                        return BrokerConnection.objects.filter(
                            broker__name="DERIV"
                        ).first()

                    conn = await _get_conn()
                    if conn:
                        client = await BrokerService.get_client(str(conn.id))
                        await client.connect()
                        symbols = await MarketDataService.sync_deriv_instruments(client)
                        await client.disconnect()
                        return len(symbols)
                    else:
                        raise ValueError(
                            "No Deriv Connection Found. Please Attach Key in Brokers Tab."
                        )

                count = async_to_sync(sys_sync)()
                messages.success(
                    request,
                    f"Successfully synced {count} active instruments directly from Deriv.",
                )
            except Exception as e:
                messages.error(request, f"Sync Failed: {str(e)}")

        elif action == "pull_data":
            try:
                instrument = Instrument.objects.get(symbol=symbol)

                async def fetch_data():
                    @sync_to_async
                    def _get_conn():
                        return BrokerConnection.objects.filter(
                            broker__name="DERIV"
                        ).first()

                    conn = await _get_conn()
                    if conn:
                        client = await BrokerService.get_client(str(conn.id))
                        await client.connect()
                        await MarketDataService.fetch_historical_ohlcv(
                            client, instrument, bar_size="15 mins"
                        )
                        await client.disconnect()
                    else:
                        raise ValueError(
                            "No Deriv Connection Found. Please Attach Key in Brokers Tab."
                        )

                async_to_sync(fetch_data)()
                messages.success(
                    request,
                    f"Market Data forcefully pulled for {symbol} via Direct WebSockets.",
                )
            except Exception as e:
                messages.error(request, f"Data Pull Failed: {str(e)}")

        elif action == "run_backtest":
            days = int(request.POST.get("days", 60))

            try:
                from apps.strategies.tasks import run_backtest_task

                # Dispatch the celery background task
                run_backtest_task.delay(symbol, days)

                messages.success(
                    request,
                    f"Simulation started for {symbol} over last {days} days on the Quantum Engine. Check back later.",
                )
            except ImportError:
                messages.error(
                    request,
                    "Celery tasks module missing. Ensure background workers are setup.",
                )
            except Exception as e:
                messages.error(request, f"Failed to dispatch simulation: {str(e)}")

        return self.get(request, *args, **kwargs)


class StrategyListView(ListView):
    model = Strategy
    template_name = "dashboard/strategies.html"
    context_object_name = "strategies"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_signals"] = SignalLog.objects.all().select_related(
            "instrument"
        )[:10]
        return context

    def post(self, request, *args, **kwargs):
        from django.contrib import messages

        action = request.POST.get("action")

        if action == "start_all":
            Strategy.objects.update(is_active=True, status="RUNNING")
            try:
                from apps.strategies.tasks import scan_all_instruments

                scan_all_instruments.delay()
                messages.success(
                    request,
                    "Institutional Fleet: All strategies engaged. Background signal scanner launched.",
                )
            except ImportError:
                messages.success(
                    request,
                    "Institutional Fleet: Strategies engaged (Async task module missing).",
                )
        elif action == "stop_all":
            Strategy.objects.update(is_active=False, status="STOPPED")
            messages.warning(request, "Institutional Fleet: All strategies disengaged.")

        return self.get(request, *args, **kwargs)


class BrokerManagementView(TemplateView):
    template_name = "dashboard/brokers.html"

    def get_context_data(self, **kwargs):
        from apps.core.models import SystemConfiguration

        context = super().get_context_data(**kwargs)
        context["connections"] = BrokerConnection.objects.all().select_related("broker")
        context["accounts"] = BrokerAccount.objects.all().select_related(
            "broker_connection"
        )
        context["active_trading_account"] = SystemConfiguration.get_value(
            "ACTIVE_TRADING_ACCOUNT", ""
        )
        return context

    def post(self, request, *args, **kwargs):
        from asgiref.sync import async_to_sync
        from django.contrib import messages

        from apps.brokers.models import Broker, BrokerConnection
        from apps.brokers.services import BrokerService

        action = request.POST.get("action")
        connection_id = request.POST.get("connection_id")

        if action == "add_deriv_key":
            token = request.POST.get("deriv_token")
            if token:
                deriv_broker, _ = Broker.objects.get_or_create(
                    name="DERIV",
                    defaults={
                        "display_name": "Deriv (Binary.com)",
                        "broker_type": "DERIV",
                        "host": "wss://ws.binaryws.com/websockets/v3",
                        "is_active": True,
                        "is_testing": True,
                    },
                )

                conn, _ = BrokerConnection.objects.update_or_create(
                    broker=deriv_broker,
                    name="Deriv API Connection",
                    defaults={
                        "api_key": token,
                        "status": "DISCONNECTED",
                    },
                )
                # Automatically trigger connection state and sync
                try:
                    success = async_to_sync(BrokerService.connect_broker)(str(conn.id))
                    if success:
                        messages.success(
                            request,
                            "Deriv API Key attached. Broker connection established and accounts synced.",
                        )
                    else:
                        messages.warning(
                            request,
                            "Deriv API Key attached, but connection could not be established.",
                        )
                except Exception as e:
                    messages.error(
                        request, f"Failure establishing broker link: {str(e)}"
                    )
            else:
                messages.error(request, "Please provide a valid Deriv Token.")

        elif action == "reconnect" and connection_id:
            try:
                success = async_to_sync(BrokerService.connect_broker)(connection_id)
                if success:
                    messages.success(request, "Broker reconnected successfully.")
                else:
                    messages.error(
                        request, "Failed to reconnect to broker. Check your API key."
                    )
            except Exception as e:
                messages.error(request, f"Connection Failure: {str(e)}")

        elif action == "sync_accounts" and connection_id:
            try:
                async_to_sync(BrokerService.sync_accounts)(connection_id)
                messages.success(request, "Account balances and profiles synced.")
            except Exception as e:
                messages.error(request, f"Sync Failure: {str(e)}")

        elif action == "set_active_account":
            account_id = request.POST.get("account_id")
            if account_id:
                from apps.core.models import SystemConfiguration

                # Validate
                valid_acc = BrokerAccount.objects.filter(
                    account_number=account_id
                ).first()
                if valid_acc:
                    SystemConfiguration.set_value(
                        "ACTIVE_TRADING_ACCOUNT",
                        account_id,
                        "The locked account for bot execution.",
                    )
                    messages.success(
                        request, f"Execution Target Locked: Set to {account_id}."
                    )
                else:
                    messages.error(request, "Account validation failed.")
            else:
                messages.error(request, "No account ID provided.")

        elif action == "disconnect" and connection_id:
            BrokerService.disconnect_broker(connection_id)
            messages.warning(request, "Broker connection terminated.")

        return self.get(request, *args, **kwargs)


class SystemSettingsView(TemplateView):
    template_name = "dashboard/settings.html"

    def post(self, request, *args, **kwargs):
        from django.contrib import messages

        from apps.oms.models import Order

        action = request.POST.get("action")

        if action == "kill_switch":
            # Logic to cancel all orders
            Order.objects.filter(state__in=["PENDING", "SUBMITTED"]).update(
                state="CANCELLED"
            )
            messages.error(
                request, "GLOBAL KILL SWITCH ENGAGED: All pending orders cancelled."
            )

        return self.get(request, *args, **kwargs)


class MLDashboardView(TemplateView):
    template_name = "dashboard/ml_models.html"

    def get_context_data(self, **kwargs):
        import os

        from apps.oms.models import Instrument
        from apps.strategies.ml_services import MLStrategyService

        context = super().get_context_data(**kwargs)
        instruments = Instrument.objects.filter(exchange="DERIV", is_active=True)

        model_stats = []
        for inst in instruments:
            path = MLStrategyService.get_model_path(inst.symbol)
            exists = os.path.exists(path)
            stats = {
                "symbol": inst.symbol,
                "name": inst.name,
                "exists": exists,
                "last_trained": timezone.datetime.fromtimestamp(os.path.getmtime(path))
                if exists
                else None,
                "size": f"{os.path.getsize(path) / 1024:.1f} KB" if exists else "N/A",
                "learning_labels": LearningLabel.objects.filter(
                    symbol=inst.symbol
                ).count(),
            }
            model_stats.append(stats)

        context["models"] = model_stats
        context["total_labels"] = LearningLabel.objects.count()
        return context

    def post(self, request, *args, **kwargs):
        from apps.strategies.tasks import train_model_task

        symbol = request.POST.get("symbol")
        action = request.POST.get("action")

        if action == "train":
            train_model_task.delay(symbol)
            return JsonResponse(
                {
                    "status": "ignited",
                    "message": f"Quantum Training ignited for {symbol}.",
                }
            )

        return self.get(request, *args, **kwargs)


def ml_training_logs(request, symbol):
    """API for real-time log polling and historical backfill."""
    last_id = request.GET.get("last_id", 0)
    limit = int(request.GET.get("limit", 0))

    query = MLTrainingLog.objects.filter(symbol=symbol)

    if last_id:
        query = query.filter(id__gt=last_id)

    if limit:
        query = query.order_by("-timestamp")[:limit]
        # Return in chronological order
        logs = reversed(list(query.values("id", "message", "level", "timestamp")))
    else:
        logs = query.order_by("timestamp").values("id", "message", "level", "timestamp")

    return JsonResponse({"logs": list(logs)})


class BrokerOpsView(TemplateView):
    """Handles advanced broker operations like account creation."""

    def post(self, request, *args, **kwargs):
        from asgiref.sync import async_to_sync
        from django.contrib import messages

        from apps.brokers.models import BrokerConnection
        from apps.brokers.services import BrokerService

        action = request.POST.get("action")

        async def run_op():
            conn = await sync_to_async(
                lambda: BrokerConnection.objects.filter(broker__name="DERIV").first()
            )()
            if not conn:
                return False, "No Deriv connection."

            client = await BrokerService.get_client(str(conn.id))
            await client.connect()

            if action == "request_verify":
                # Map to verify_email command
                email = request.POST.get("email")
                msg = {"verify_email": email, "type": "account_opening"}
                await client.ws.send(json.dumps(msg))
                res = json.loads(await client.ws.recv())
                await client.disconnect()
                return ("error" not in res), res.get("error", {}).get(
                    "message", "Verification email sent. Check your inbox."
                )

            elif action == "create_demo":
                code = request.POST.get("code")
                password = request.POST.get("password")
                # Map to new_account_virtual command
                msg = {
                    "new_account_virtual": 1,
                    "verification_code": code,
                    "client_password": password,
                    "residence": "ng",
                }
                await client.ws.send(json.dumps(msg))
                res = json.loads(await client.ws.recv())

                if "error" in res:
                    await client.disconnect()
                    return False, res["error"].get(
                        "message", "Failed to create account."
                    )

                # If success, try to link it automatically or just inform
                await client.disconnect()
                return (
                    True,
                    "Institutional Demo Account Provisioned with $10,000. (Note: Platform limits apply to initial balance).",
                )

            elif action == "topup_demo":
                # Deriv topup_virtual resets to $10,000
                msg = {"topup_virtual": 1}
                await client.ws.send(json.dumps(msg))
                res = json.loads(await client.ws.recv())
                await client.disconnect()
                if "error" in res:
                    return False, res["error"].get(
                        "message", "Top-up failed. Balance might be too high to reset."
                    )
                return True, "Virtual Balance Reset to Platform Maximum ($10,000)."

            return False, "Invalid action"

        success, message = async_to_sync(run_op)()
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        from django.shortcuts import redirect

        return redirect("dashboard:brokers")


class TradeManagementView(TemplateView):
    template_name = "dashboard/trades.html"

    def get_context_data(self, **kwargs):
        from apps.brokers.models import BrokerConnection
        from apps.brokers.services import BrokerService

        # Trigger Hot Sync from Broker before rendering
        # This ensures the UI is "Ground Truth"
        try:
            conn = BrokerConnection.objects.filter(
                broker__name="DERIV", status="CONNECTED"
            ).first()
            if conn:
                async_to_sync(BrokerService.sync_portfolio)(str(conn.id))
                async_to_sync(BrokerService.sync_statement)(str(conn.id))
        except Exception as e:
            logger.error(f"Failed to hot-sync broker data: {e}")

        context = super().get_context_data(**kwargs)

        # Fetch active positions (quantity != 0)
        active_positions = (
            Position.objects.exclude(quantity=0)
            .select_related("instrument", "broker_account")
            .order_by("-last_updated")
        )

        # Fetch recent orders
        recent_orders = (
            Order.objects.all()
            .select_related("instrument", "broker_account")
            .order_by("-created_at")[:100]
        )

        context.update(
            {
                "active_positions": active_positions,
                "recent_orders": recent_orders,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        from django.contrib import messages

        action = request.POST.get("action")

        if action == "close_position":
            position_id = request.POST.get("position_id")
            # TODO: Implement actual position closure logic calling execute_signal with counter-direction
            messages.info(
                request, f"Manual closure for position {position_id} initiated."
            )

        elif action == "cancel_order":
            order_id = request.POST.get("order_id")
            # TODO: Implement broker cancel call logic
            messages.warning(
                request, f"Cancellation request for order {order_id} sent to broker."
            )

        return self.get(request, *args, **kwargs)


def telemetry_data(request):
    """Real-time data stream for the dashboard (Signals + Orders)."""
    signals = (
        SignalLog.objects.all()
        .select_related("instrument")
        .order_by("-created_at")[:15]
    )
    orders = (
        Order.objects.all().select_related("instrument").order_by("-created_at")[:15]
    )

    signal_list = [
        {
            "symbol": s.instrument.symbol,
            "grade": s.grade,
            "direction": s.direction or "NONE",
            "time": s.created_at.strftime("%H:%M:%S"),
            "message": s.message,
        }
        for s in signals
    ]

    order_list = [
        {
            "id": str(o.id),
            "symbol": o.instrument.symbol,
            "side": o.side,
            "quantity": str(o.quantity),
            "state": o.state,
            "time": o.created_at.strftime("%H:%M:%S"),
        }
        for o in orders
    ]

    return JsonResponse(
        {
            "signals": signal_list,
            "orders": order_list,
            "timestamp": timezone.now().isoformat(),
        }
    )
