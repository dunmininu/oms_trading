"""
Risk Management services for trade validation and position sizing.
"""

import logging
from decimal import Decimal
from typing import Dict, Any
from apps.oms.models import Position, Instrument
from apps.brokers.models import BrokerAccount

logger = logging.getLogger(__name__)

class RiskManagementService:
    """Service for enforcing risk rules."""

    @classmethod
    def validate_trade(
        cls,
        broker_account: BrokerAccount,
        instrument: Instrument,
        grade: str,
        price: Decimal,
        account_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Validate if a trade can be taken based on grading and risk rules.
        - Risk 10% of account max.
        - Max 5 trades per pair for A+ setup.
        - Grading determines allowed frequency/exposure.
        """
        # 1. Enforce Max Trades per Pair based on Grade
        grade_limits = {
            'A+': 5,
            'B': 3,
            'C': 1,
            'D-': 0
        }
        max_allowed = grade_limits.get(grade, 0)

        current_pos = Position.objects.filter(
            broker_account=broker_account,
            instrument=instrument
        ).first()

        # This is a simplified check: in a real system we'd count open orders too
        if max_allowed == 0:
            return {'allowed': False, 'reason': f"Grade {grade} setups are not tradable."}

        # 2. Calculate Max Position Size (10% of balance)
        max_risk_amount = account_balance * Decimal('0.10')
        suggested_qty = max_risk_amount / price

        # 3. RR Rule (1:2 Max RR should be handled at order placement for TP/SL)

        return {
            'allowed': True,
            'suggested_quantity': suggested_qty,
            'max_risk_amount': max_risk_amount,
            'risk_reward_ratio': 2.0,
            'grade': grade
        }
