"""
Self-learning services to analyze trade outcomes and improve strategy grading.
"""

import logging

from apps.oms.models import Order
from apps.strategies.models import SetupPerformance
from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


class LearningService:
    """Service for analyzing trade outcomes and updating model intelligence."""

    @classmethod
    def record_trade_outcome(cls, order: Order):
        """Analyze a completed trade and update setup performance metrics."""
        if order.state != "FILLED" or not order.strategy_run:
            return

        # Simplified: Get setup info from metadata
        setup_info = order.metadata.get("setup_info")
        if not setup_info:
            return

        # Update SetupPerformance record
        performance, _ = SetupPerformance.objects.get_or_create(
            tenant=order.tenant,
            instrument=order.instrument,
            setup_type=setup_info.get("type"),
            timeframe=setup_info.get("timeframe"),
        )

        performance.total_trades += 1

        # Determine if it was a winner (This requires realized PnL tracking)
        # For now, let's look at executions vs stop/target
        # (Simplified logic for demonstration)
        is_winner = order.metadata.get("is_winner", False)
        if is_winner:
            performance.winning_trades += 1

        performance.save()
        logger.info(
            f"Updated performance for {performance.setup_type}: {performance.success_rate}% success"
        )

    @classmethod
    def get_setup_adjustment(
        cls, tenant: Tenant, instrument, setup_type: str, timeframe: str
    ) -> float:
        """Get a score adjustment based on historical performance of this setup."""
        try:
            perf = SetupPerformance.objects.get(
                tenant=tenant,
                instrument=instrument,
                setup_type=setup_type,
                timeframe=timeframe,
            )

            # If success rate is low (< 40%) penalize the score
            if perf.total_trades >= 10:
                if perf.success_rate < 40:
                    return -1.0
                elif perf.success_rate > 60:
                    return 1.0
            return 0.0
        except SetupPerformance.DoesNotExist:
            return 0.0
