"""
ICT Strategy detection services.
"""

import logging
from typing import Any

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)


class ICTSetupService:
    """Service for detecting ICT setups (FVG and Liquidity Sweeps)."""

    @classmethod
    def detect_fvg(
        cls, instrument: Instrument, interval: str, df_bars=None
    ) -> list[dict[str, Any]]:
        """
        Detect Fair Value Gaps (FVG).
        A bullish FVG occurs when the low of candle 3 is above the high of candle 1.
        A bearish FVG occurs when the high of candle 3 is below the low of candle 1.
        """
        if df_bars is not None:
            # Handle backtest data (Pandas DataFrame)
            if len(df_bars) < 3:
                return []
            fvgs = []
            for i in range(len(df_bars) - 2):
                b1 = df_bars.iloc[i]
                b2 = df_bars.iloc[i + 1]
                b3 = df_bars.iloc[i + 2]

                # Institutional Displacement Check: Candle 2 must be significant
                body_2 = abs(float(b2["close"]) - float(b2["open"]))
                avg_body = (
                    df_bars.iloc[max(0, i - 5) : i + 1]
                    .apply(lambda x: abs(float(x["close"]) - float(x["open"])), axis=1)
                    .mean()
                )

                # Displacement requirement: Body of b2 > 1.3x previous avg body OR > 50% of its own range
                is_displaced = body_2 > (avg_body * 1.3) or body_2 > (
                    abs(float(b2["high"]) - float(b2["low"])) * 0.5
                )

                if float(b3["low"]) > float(b1["high"]) and is_displaced:
                    fvgs.append(
                        {
                            "type": "BULLISH",
                            "direction": 1,
                            "top": b3["low"],
                            "bottom": b1["high"],
                        }
                    )
                elif float(b3["high"]) < float(b1["low"]) and is_displaced:
                    fvgs.append(
                        {
                            "type": "BEARISH",
                            "direction": -1,
                            "top": b1["low"],
                            "bottom": b3["high"],
                        }
                    )
            return fvgs

        # Original live logic
        bars = list(
            HistoricalData.objects.filter(
                instrument=instrument, interval=interval, data_type="OHLC"
            ).order_by("start_time")
        )

        if len(bars) < 3:
            return []

        fvgs = []
        for i in range(len(bars) - 2):
            b1 = bars[i]
            b2 = bars[i + 1]
            b3 = bars[i + 2]

            # Bullish FVG (Gap between B1 High and B3 Low)
            if b3.low_price > b1.high_price:
                # Institutional SL: Bottom of the move (B1 Low)
                sl = float(b1.low_price)
                entry = float(b3.low_price)
                risk = entry - sl
                # Target at least 2:1 RR or use recent highs if we expand this
                tp = entry + (risk * 2)

                fvgs.append(
                    {
                        "type": "BULLISH",
                        "top": b3.low_price,
                        "bottom": b1.high_price,
                        "sl_price": sl,
                        "tp_price": tp,
                        "start_time": b2.start_time,
                        "instrument": instrument.symbol,
                    }
                )

            # Bearish FVG (Gap between B1 Low and B3 High)
            elif b3.high_price < b1.low_price:
                # Institutional SL: Top of the move (B1 High)
                sl = float(b1.high_price)
                entry = float(b3.high_price)
                risk = sl - entry
                tp = entry - (risk * 2)

                fvgs.append(
                    {
                        "type": "BEARISH",
                        "top": b1.low_price,
                        "bottom": b3.high_price,
                        "sl_price": sl,
                        "tp_price": tp,
                        "start_time": b2.start_time,
                        "instrument": instrument.symbol,
                    }
                )

        return fvgs

    @classmethod
    def detect_liquidity_sweeps(
        cls, instrument: Instrument, interval: str, df_bars=None
    ) -> list[dict[str, Any]]:
        """
        Detect Liquidity Sweeps.
        A sweep occurs when price moves beyond a previous swing high/low and then reverses.
        """
        if df_bars is not None:
            if len(df_bars) < 10:
                return []
            recent_high = df_bars.iloc[:-5]["high"].max()
            recent_low = df_bars.iloc[:-5]["low"].min()
            last_bar = df_bars.iloc[-1]
            if last_bar["high"] > recent_high and last_bar["close"] < recent_high:
                return [{"type": "BEARISH_SWEEP", "direction": -1}]
            if last_bar["low"] < recent_low and last_bar["close"] > recent_low:
                return [{"type": "BULLISH_SWEEP", "direction": 1}]
            return []

        bars = list(
            HistoricalData.objects.filter(
                instrument=instrument, interval=interval, data_type="OHLC"
            ).order_by("-start_time")[:50]
        )

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
                sweeps.append(
                    {
                        "type": "BEARISH_SWEEP",
                        "level": recent_high,
                        "time": b.start_time,
                        "instrument": instrument.symbol,
                    }
                )
            # Bullish Sweep (Swept Low)
            if b.low_price < recent_low and b.close_price > recent_low:
                sweeps.append(
                    {
                        "type": "BULLISH_SWEEP",
                        "level": recent_low,
                        "time": b.start_time,
                        "instrument": instrument.symbol,
                    }
                )

        return sweeps
