"""
ICT Strategy detection services.
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)

class ICTSetupService:
    """Service for detecting ICT setups (FVG and Liquidity Sweeps)."""

    @classmethod
    def detect_fvg(cls, instrument: Instrument, interval: str, df_bars=None) -> List[Dict[str, Any]]:
        """
        Detect Fair Value Gaps (FVG).
        A bullish FVG occurs when the low of candle 3 is above the high of candle 1.
        A bearish FVG occurs when the high of candle 3 is below the low of candle 1.
        """
        if df_bars is not None:
            # Handle backtest data (Pandas DataFrame)
            if len(df_bars) < 3: return []
            fvgs = []
            for i in range(len(df_bars) - 2):
                b1 = df_bars.iloc[i]
                b3 = df_bars.iloc[i+2]
                if float(b3['low']) > float(b1['high']):
                    fvgs.append({'type': 'BULLISH', 'direction': 1, 'top': b3['low'], 'bottom': b1['high']})
                elif float(b3['high']) < float(b1['low']):
                    fvgs.append({'type': 'BEARISH', 'direction': -1, 'top': b1['low'], 'bottom': b3['high']})
            return fvgs

        # Original live logic
        bars = list(HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).order_by('start_time'))

        if len(bars) < 3:
            return []

        fvgs = []
        for i in range(len(bars) - 2):
            b1 = bars[i]
            b2 = bars[i+1]
            b3 = bars[i+2]

            # Bullish FVG
            if b3.low_price > b1.high_price:
                fvgs.append({
                    'type': 'BULLISH',
                    'top': b3.low_price,
                    'bottom': b1.high_price,
                    'start_time': b2.start_time,
                    'instrument': instrument.symbol
                })

            # Bearish FVG
            elif b3.high_price < b1.low_price:
                fvgs.append({
                    'type': 'BEARISH',
                    'top': b1.low_price,
                    'bottom': b3.high_price,
                    'start_time': b2.start_time,
                    'instrument': instrument.symbol
                })

        return fvgs

    @classmethod
    def detect_liquidity_sweeps(cls, instrument: Instrument, interval: str, df_bars=None) -> List[Dict[str, Any]]:
        """
        Detect Liquidity Sweeps.
        A sweep occurs when price moves beyond a previous swing high/low and then reverses.
        """
        if df_bars is not None:
            if len(df_bars) < 10: return []
            recent_high = df_bars.iloc[:-5]['high'].max()
            recent_low = df_bars.iloc[:-5]['low'].min()
            last_bar = df_bars.iloc[-1]
            if last_bar['high'] > recent_high and last_bar['close'] < recent_high:
                return [{'type': 'BEARISH_SWEEP', 'direction': -1}]
            if last_bar['low'] < recent_low and last_bar['close'] > recent_low:
                return [{'type': 'BULLISH_SWEEP', 'direction': 1}]
            return []

        bars = list(HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).order_by('-start_time')[:50])

        if len(bars) < 10:
            return []

        sweeps = []
        # Find Swing High/Low in the first 40 bars
        recent_high = max(b.high_price for b in bars[5:])
        recent_low = min(b.low_price for b in bars[5:])

        # Check if the most recent 5 bars swept these levels
        for i in range(5):
            b = bars[i]
            # Bearish Sweep (Swept High)
            if b.high_price > recent_high and b.close_price < recent_high:
                sweeps.append({
                    'type': 'BEARISH_SWEEP',
                    'level': recent_high,
                    'time': b.start_time,
                    'instrument': instrument.symbol
                })
            # Bullish Sweep (Swept Low)
            if b.low_price < recent_low and b.close_price > recent_low:
                sweeps.append({
                    'type': 'BULLISH_SWEEP',
                    'level': recent_low,
                    'time': b.start_time,
                    'instrument': instrument.symbol
                })

        return sweeps
