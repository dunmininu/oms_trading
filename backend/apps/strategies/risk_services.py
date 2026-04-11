"""
Risk Management services including Kelly Criterion and setup validation.
"""

import logging
from decimal import Decimal
from typing import Any

from apps.brokers.models import BrokerAccount
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)


class RiskManagementService:
    """Service for advanced risk management and position sizing."""

    @classmethod
    def calculate_kelly_size(
        cls, win_prob: float, win_loss_ratio: float = 2.0
    ) -> float:
        """
        Calculate trade size using Kelly Criterion.
        K% = W - [(1 - W) / R]
        W: Win probability (0-1)
        R: Win/Loss ratio (2.0 for our 1:2 RR)
        """
        # Using "Half-Kelly" for safer retail trading
        kelly_pct = win_prob - ((1 - win_prob) / win_loss_ratio)
        half_kelly = max(0, kelly_pct / 2)
        # Cap at 10% as per user requirements
        return min(half_kelly, 0.10)

    @classmethod
    def validate_trade(
        cls,
        broker_account: BrokerAccount,
        instrument: Instrument,
        grade: str,
        price: Decimal,
        account_balance: Decimal,
        win_probability: float = 0.5,
    ) -> dict[str, Any]:
        """
        Validate trade and calculate dynamic position size using Kelly Criterion.
        """
        grade_limits = {"A+": 5, "A": 4, "B": 3, "C": 1, "D-": 0}
        max_allowed = grade_limits.get(grade, 0)

        if max_allowed == 0:
            return {
                "allowed": False,
                "reason": f"Grade {grade} setups are not tradable.",
            }

        # Dynamic Risk Amount using Half-Kelly
        risk_fraction = cls.calculate_kelly_size(win_probability)
        if risk_fraction <= 0:
            return {
                "allowed": False,
                "reason": f"Negative Kelly expectancy ({win_probability:.2f})",
            }

        max_risk_amount = account_balance * Decimal(str(risk_fraction))
        # Ensure minimum 1% risk if A+ setup but Kelly is low
        if grade == "A+" and max_risk_amount < account_balance * Decimal("0.01"):
            max_risk_amount = account_balance * Decimal("0.01")

        suggested_qty = max_risk_amount / price

        return {
            "allowed": True,
            "suggested_quantity": suggested_qty,
            "max_risk_amount": max_risk_amount,
            "risk_percent": float(risk_fraction * 100),
            "risk_reward_ratio": 2.0,
            "grade": grade,
        }
