import logging
from datetime import timedelta

from celery import shared_task

from apps.oms.models import Instrument
from apps.strategies.grading_services import GradingService
from apps.strategies.models import BacktestResult, SignalLog
from apps.strategies.services import BacktestService

logger = logging.getLogger(__name__)


@shared_task(name="apps.strategies.tasks.keep_brokers_alive")
def keep_brokers_alive():
    """Heartbeat task to keep Deriv WebSockets from timing out."""

    from asgiref.sync import async_to_sync

    from apps.brokers.models import BrokerConnection
    from apps.brokers.services import BrokerService

    conns = BrokerConnection.objects.filter(
        status="CONNECTED", broker__broker_type="DERIV"
    )
    for conn in conns:

        async def _ping(c=conn):
            try:
                client = await BrokerService.get_client(str(c.id))
                if client.is_connected:
                    success = await client.ping()
                    if success:
                        logger.info(f"Heartbeat: Ping sent to {c.name}")
                    else:
                        logger.warning(
                            f"Heartbeat: Ping failed for {c.name}, attempting recovery."
                        )
                        await client.connect()
                else:
                    logger.info(
                        f"Heartbeat: Connection {c.name} is down, attempting wake-up."
                    )
                    await client.connect()
            except Exception as e:
                logger.error(f"Heartbeat Failure for {c.name}: {e}")

        async_to_sync(_ping)()


@shared_task(name="apps.strategies.tasks.scan_all_instruments")
def scan_all_instruments():
    """Distributed task to trigger setup detection for all active instruments."""
    instruments = Instrument.objects.filter(is_active=True)
    logger.info(
        f"Engaging Autonomous Fleet: Scanning {instruments.count()} instruments..."
    )

    for instrument in instruments:
        # Dispatch individual scan task per instrument
        scan_instrument_setup.delay(instrument.id)


@shared_task(name="apps.strategies.tasks.scan_instrument_setup")
def scan_instrument_setup(instrument_id):
    """Scan a specific instrument."""
    try:
        instrument = Instrument.objects.get(id=instrument_id)
        logger.debug(f"[RADAR] Scanning {instrument.symbol} for ICT/Quant signature...")

        # This will run ICT + Quant + ML Grading
        grading_result = GradingService.grade_setup(instrument, "15_MINUTE")

        logger.info(
            f"[RADAR][{instrument.symbol}] Grade: {grading_result['grade']} (Score: {grading_result['score']})"
        )

        if grading_result["grade"] in ["A+", "B"]:
            logger.info(
                f"SIGNAL FOUND: {instrument.symbol} - Grade {grading_result['grade']}"
            )

            # Persist signal to DB
            SignalLog.objects.create(
                instrument=instrument,
                strategy_name="Institutional Scanner",
                setup_type=grading_result.get("setup_type", "ICT_QUANT"),
                timeframe="15_MINUTE",
                grade=grading_result["grade"],
                direction=grading_result["direction"],
                message=f"Setup Detected: {grading_result['grade']} grade hit on {instrument.symbol}.",
            )
            # 3. Trigger Autonomous Execution if bot is enabled
            try:
                from apps.strategies.execution_services import (
                    AutonomousExecutionService,
                )
                from apps.strategies.models import Strategy

                # Look for the master sovereign bot configuration
                bot = Strategy.objects.filter(
                    name="Institutional Sovereign Bot", is_active=True
                ).first()
                if bot and bot.auto_start:
                    AutonomousExecutionService.execute_signal(
                        instrument, grading_result
                    )
            except Exception as e:
                logger.error(f"Autonomous Execution ignition failed: {e}")

    except Exception as e:
        logger.error(f"Error scanning instrument {instrument_id}: {e}")


@shared_task(name="apps.strategies.tasks.run_backtest_task")
def run_backtest_task(symbol: str, days: int):
    """Run backtesting in the background with status tracking."""

    from django.utils import timezone

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # 1. Initialize result record with RUNNING status
    try:
        instrument = Instrument.objects.get(symbol=symbol)
    except Instrument.DoesNotExist:
        logger.error(f"Cannot backtest: Instrument {symbol} not found.")
        return {"status": "error", "message": "Instrument not found"}

    bt = BacktestResult.objects.create(
        instrument=instrument,
        start_date=start_date,
        end_date=end_date,
        status="RUNNING",
    )

    try:
        # 2. Execute simulation
        logger.info(
            f"[TASK][{symbol}] Starting Quantum Simulation via BacktestService..."
        )
        engine = BacktestService()

        # Check if we need to sync data or train model (internal to engine.run)
        logger.info(f"[TASK][{symbol}] Pre-flight data checks initiated...")

        results = engine.run(symbol, start_date, end_date)

        logger.info(
            f"[TASK][{symbol}] Engine completed. Matched {results.get('total_setups', 0)} setups, Executed {results.get('total_trades', 0)} trades."
        )

        if "error" in results:
            bt.status = "FAILED"
            bt.error_reason = results["error"]
            bt.save()
            return {"status": "error", "message": results["error"]}

        # 3. Update record with results
        bt.status = "COMPLETED"
        bt.total_trades = results.get("total_trades", 0)
        bt.total_setups = results.get("total_setups", 0)
        bt.rejected_setups = results.get("rejected_setups", 0)
        bt.win_rate = results.get("win_rate", 0)
        bt.total_pnl = results.get("total_pnl", 0)
        bt.final_equity = results.get("final_equity", 0)
        bt.equity_curve = results.get("equity_curve", [])
        bt.metrics_json = results.get("metrics_json", {})

        # Guard: If trades are 0, make sure pnl is explicit 0.0
        if bt.total_trades == 0:
            bt.total_pnl = 0.0

        bt.save()
        logger.info(f"[TASK][{symbol}] Result {bt.id} locked and saved.")

        return {
            "status": "success",
            "backtest_id": str(bt.id),
            "pnl": float(bt.total_pnl),
        }

    except Exception as e:
        import traceback

        error_msg = str(e)
        logger.error(f"Quantum Engine Failure for {symbol}: {error_msg}")

        bt.status = "FAILED"
        bt.error_reason = f"{error_msg}\n{traceback.format_exc()}"
        bt.save()
        return {"status": "error", "message": error_msg}


@shared_task(name="apps.strategies.tasks.train_model_task")
def train_model_task(symbol: str):
    """Background task to train or recalibrate an XGBoost model."""
    try:
        from apps.oms.models import Instrument
        from apps.strategies.ml_services import MLStrategyService

        instrument = Instrument.objects.get(symbol=symbol)
        service = MLStrategyService()
        service.train_model(instrument, "15_MINUTE")
        return {"status": "success", "symbol": symbol}
    except Exception as e:
        logger.error(f"Training failed for {symbol}: {e}")
        return {"status": "error", "message": str(e)}
