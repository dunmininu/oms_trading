"""
Quantitative analysis services including Mean Reversion, Momentum, and Black-Scholes.
"""

import math
import logging
from typing import Dict, Any, List
from decimal import Decimal
from scipy.stats import norm
from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)

class QuantService:
    """Service for quantitative models."""

    @classmethod
    def calculate_rsi(cls, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI) for momentum."""
        if len(prices) <= period:
            return 50.0

        deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        gain = [d if d > 0 else 0 for d in deltas]
        loss = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gain[:period]) / period
        avg_loss = sum(loss[:period]) / period

        if avg_loss == 0: return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1+rs))

    @classmethod
    def calculate_z_score(cls, prices: List[float], period: int = 20) -> float:
        """Calculate Z-Score for mean reversion."""
        if len(prices) < period:
            return 0.0

        recent_prices = prices[-period:]
        mean = sum(recent_prices) / period
        variance = sum((p - mean) ** 2 for p in recent_prices) / period
        std_dev = math.sqrt(variance)

        if std_dev == 0: return 0.0
        return (recent_prices[-1] - mean) / std_dev

    @classmethod
    def black_scholes(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'CALL'
    ) -> float:
        """
        Calculate Black-Scholes option price.
        S: Spot price
        K: Strike price
        T: Time to expiration (years)
        r: Risk-free rate
        sigma: Volatility
        """
        try:
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            if option_type == 'CALL':
                return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:
                return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        except Exception as e:
            logger.error(f"Black-Scholes error: {e}")
            return 0.0

    @classmethod
    def get_market_regime(cls, instrument: Instrument, interval: str) -> Dict[str, Any]:
        """Determine market regime using RSI and Z-Score."""
        bars = HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).order_by('-start_time')[:50]

        if not bars:
            return {'rsi': 50, 'z_score': 0, 'regime': 'NEUTRAL'}

        prices = [float(b.close_price) for b in reversed(bars)]
        rsi = cls.calculate_rsi(prices)
        z_score = cls.calculate_z_score(prices)

        regime = 'NEUTRAL'
        if rsi > 70: regime = 'OVERBOUGHT'
        elif rsi < 30: regime = 'OVERSOLD'

        return {
            'rsi': rsi,
            'z_score': z_score,
            'regime': regime
        }
