"""
Quantitative analysis services including Mean Reversion, Momentum, and Black-Scholes.
"""

<<<<<<< HEAD
import math
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from decimal import Decimal
from scipy.stats import norm
=======
import logging
import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

>>>>>>> origin/main
from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)

<<<<<<< HEAD
=======

>>>>>>> origin/main
class QuantService:
    """Service for quantitative models using vectorized calculations."""

    @classmethod
<<<<<<< HEAD
    def calculate_rsi(cls, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using Pandas for vectorized operations."""
        if len(prices) <= period:
            return 50.0

        series = pd.Series(prices)
        delta = series.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

=======
    def calculate_rsi(cls, prices: list[float], period: int = 14) -> float:
        """Calculate RSI using Pandas for vectorized operations."""
        if len(prices) <= period:
            return 50.0

        series = pd.Series(prices)
        delta = series.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

>>>>>>> origin/main
        val = rsi.iloc[-1]
        return float(val) if not np.isnan(val) else 50.0

    @classmethod
<<<<<<< HEAD
    def calculate_z_score(cls, prices: List[float], period: int = 20) -> float:
        """Calculate Z-Score using Pandas."""
        if len(prices) < period:
            return 0.0

        series = pd.Series(prices)
        rolling_mean = series.rolling(window=period).mean()
        rolling_std = series.rolling(window=period).std()

=======
    def calculate_z_score(cls, prices: list[float], period: int = 20) -> float:
        """Calculate Z-Score using Pandas."""
        if len(prices) < period:
            return 0.0

        series = pd.Series(prices)
        rolling_mean = series.rolling(window=period).mean()
        rolling_std = series.rolling(window=period).std()

>>>>>>> origin/main
        z_scores = (series - rolling_mean) / rolling_std
        val = z_scores.iloc[-1]
        return float(val) if not np.isnan(val) else 0.0

    @classmethod
<<<<<<< HEAD
    def black_scholes(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'CALL'
=======
    def calculate_atr(cls, df_bars: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range (ATR) using Pandas."""
        if len(df_bars) < period:
            return 0.0

        high_low = df_bars["high"] - df_bars["low"]
        high_cp = (df_bars["high"] - df_bars["close"].shift()).abs()
        low_cp = (df_bars["low"] - df_bars["close"].shift()).abs()

        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        val = atr.iloc[-1]
        return float(val) if not np.isnan(val) else 0.0

    @classmethod
    def black_scholes(
        cls,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "CALL",
>>>>>>> origin/main
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
<<<<<<< HEAD
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            if option_type == 'CALL':
=======
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            if option_type == "CALL":
>>>>>>> origin/main
                return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:
                return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        except Exception as e:
            logger.error(f"Black-Scholes error: {e}")
            return 0.0

    @classmethod
<<<<<<< HEAD
    def get_market_regime(cls, instrument: Instrument, interval: str) -> Dict[str, Any]:
        """Determine market regime using RSI and Z-Score."""
        bars = HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).order_by('-start_time')[:50]

        if not bars:
            return {'rsi': 50, 'z_score': 0, 'regime': 'NEUTRAL'}
=======
    def get_market_regime(cls, instrument: Instrument, interval: str) -> dict[str, Any]:
        """Determine market regime using RSI and Z-Score."""
        bars = HistoricalData.objects.filter(
            instrument=instrument, interval=interval, data_type="OHLC"
        ).order_by("-start_time")[:50]

        if not bars:
            return {"rsi": 50, "z_score": 0, "regime": "NEUTRAL"}
>>>>>>> origin/main

        prices = [float(b.close_price) for b in reversed(bars)]
        rsi = cls.calculate_rsi(prices)
        z_score = cls.calculate_z_score(prices)

<<<<<<< HEAD
        regime = 'NEUTRAL'
        if rsi > 70: regime = 'OVERBOUGHT'
        elif rsi < 30: regime = 'OVERSOLD'

        return {
            'rsi': rsi,
            'z_score': z_score,
            'regime': regime
        }

    @classmethod
    def calculate_indicators(cls, df_bars: pd.DataFrame) -> Dict[str, Any]:
        """Calculates quantitative indicators for a given set of bars (backtest helper)."""
        prices = df_bars['close'].astype(float).tolist()
        rsi = cls.calculate_rsi(prices)
        z_score = cls.calculate_z_score(prices)
        regime = 'NEUTRAL'
        if rsi > 70: regime = 'OVERBOUGHT'
        elif rsi < 30: regime = 'OVERSOLD'
        return {'rsi': rsi, 'z_score': z_score, 'regime': regime}
=======
        regime = "NEUTRAL"
        if rsi > 65:
            regime = "OVERBOUGHT"
        elif rsi < 35:
            regime = "OVERSOLD"

        return {"rsi": rsi, "z_score": z_score, "regime": regime}

    @classmethod
    def calculate_indicators(cls, df_bars: pd.DataFrame) -> dict[str, Any]:
        """Calculates quantitative indicators for a given set of bars (backtest helper)."""
        prices = df_bars["close"].astype(float).tolist()
        rsi = cls.calculate_rsi(prices)
        z_score = cls.calculate_z_score(prices)
        regime = "NEUTRAL"
        if rsi > 65:
            regime = "OVERBOUGHT"
        elif rsi < 35:
            regime = "OVERSOLD"

        atr = cls.calculate_atr(df_bars)

        return {"rsi": rsi, "z_score": z_score, "regime": regime, "atr": atr}
>>>>>>> origin/main
