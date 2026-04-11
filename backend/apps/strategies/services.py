<<<<<<< HEAD

class BacktestService:
    """Institutional-grade backtesting engine for ICT and Quant strategies."""

    def __init__(self, tenant, initial_capital=100000.0):
        self.tenant = tenant
        self.capital = initial_capital
        self.equity = initial_capital
        self.positions = []  # List of open simulated positions
        self.trades = []     # List of completed trade results
        self.equity_curve = []

        from .ict_services import ICTSetupService
        from .quant_services import QuantService
        from .ml_services import MLStrategyService
        from .grading_services import GradingService
        from .risk_services import RiskManagementService

=======
import logging
import os
from decimal import Decimal

import pandas as pd
from asgiref.sync import sync_to_async

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

from .grading_services import GradingService
from .ict_services import ICTSetupService
from .ml_services import MLStrategyService
from .quant_services import QuantService
from .risk_services import RiskManagementService

logger = logging.getLogger(__name__)


class BacktestService:
    """Institutional-grade backtesting engine for ICT and Quant strategies."""

    def __init__(self, initial_capital=100000.0):
        self.capital = initial_capital
        self.equity = initial_capital
        self.positions = []  # List of open simulated positions
        self.trades = []  # List of completed trade results
        self.equity_curve = []

        # Intelligence tracking
        self.total_setups = 0
        self.rejected_setups = 0
        self.confluence_counts = {"ICT": 0, "Quant": 0, "ML": 0}
        self.rejected_reasons = {"GRADE": 0, "ML": 0, "RISK": 0, "VOLATILITY": 0}
        self.max_drawdown = 0
        self.peak_equity = initial_capital

>>>>>>> origin/main
        self.ict_service = ICTSetupService()
        self.quant_service = QuantService()
        self.ml_service = MLStrategyService()
        self.grading_service = GradingService()
        self.risk_service = RiskManagementService()

<<<<<<< HEAD
    def run(self, symbol, start_date, end_date, interval='15_MINUTE'):
        """Runs a backtest over a specified period."""
        from apps.marketdata.models import HistoricalData
        from apps.oms.models import Instrument
        import pandas as pd
        from decimal import Decimal

        instrument = Instrument.objects.get(symbol=symbol)

        # Load historical bars
        bars = HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            start_time__range=(start_date, end_date)
        ).order_by('start_time')

        if not bars.exists():
            return {"error": "No historical data found for period"}

        df = pd.DataFrame(list(bars.values('start_time', 'open_price', 'high_price', 'low_price', 'close_price', 'volume')))
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # Simulation Loop
        for i in range(50, len(df)):  # Need lookback for indicators
            current_bar = df.iloc[i]
            window = df.iloc[i-50:i+1]

            # 1. Update existing positions
            self._update_positions(current_bar)

            # 2. Check for new setups (Limit entries to prevent over-trading in simulation)
            if len(self.positions) >= 3:
                continue

            # Detect FVG only on the latest 3 bars
            ict_signals = self.ict_service.detect_fvg(instrument, interval, df_bars=window.iloc[-3:])

            if not ict_signals:
                ict_signals = self.ict_service.detect_liquidity_sweeps(instrument, interval, df_bars=window)

            if ict_signals:
                setup = ict_signals[-1]
                quant_data = self.quant_service.calculate_indicators(window)
                ml_prob = self.ml_service.predict_success(setup, quant_data)

                grade_result = self.grading_service.grade_setup(
                    instrument, interval, tenant=self.tenant,
                    backtest_setup=setup,
                    backtest_quant=quant_data, backtest_ml_prob=ml_prob
                )
                grade = grade_result['grade']

                if grade in ['A+', 'A', 'B']:
                    # Execute entry
                    risk_check = self.risk_service.validate_trade(
                        None, instrument, grade, Decimal(str(current_bar['close'])),
                        Decimal(str(self.equity)), win_probability=ml_prob
                    )

                    if risk_check['allowed']:
                        self._enter_trade(current_bar, setup, risk_check['suggested_quantity'], grade)

            self.equity_curve.append({
                'timestamp': str(current_bar['timestamp']),
                'equity': float(self.equity)
            })

        return self._get_results()

    def _enter_trade(self, bar, setup, quantity, grade):
        # Entry simulation with 1 tick slippage
        entry_price = float(bar['close'])
        tp = entry_price + (setup['direction'] * entry_price * 0.02) # 2% target
        sl = entry_price - (setup['direction'] * entry_price * 0.01) # 1% stop

        self.positions.append({
            'type': setup['type'],
            'direction': setup['direction'],
            'entry_price': entry_price,
            'quantity': float(quantity),
            'tp': tp,
            'sl': sl,
            'grade': grade
        })

    def _update_positions(self, bar):
        high = float(bar['high'])
        low = float(bar['low'])

=======
    def run(self, symbol, start_date, end_date, interval="15_MINUTE"):
        """Runs a backtest over a specified period."""
        self.mode = "BACKTEST"

        instrument = Instrument.objects.get(symbol=symbol)

        # 0. Data Warmup: Ensure we have at least 500 bars for a valid backtest
        bars_count = HistoricalData.objects.filter(
            instrument=instrument, interval=interval
        ).count()
        if bars_count < 500:
            from asgiref.sync import async_to_sync

            from apps.brokers.services import BrokerService
            from apps.marketdata.services import MarketDataService

            logger.info(
                f"Insufficient data for {symbol} ({bars_count} bars). Engaging Auto-Sync..."
            )

            async def sync_flow():
                from apps.brokers.models import BrokerConnection

                conn = await sync_to_async(
                    lambda: BrokerConnection.objects.filter(
                        broker__name="DERIV"
                    ).first()
                )()
                if conn:
                    client = await BrokerService.get_client(str(conn.id))
                    await client.connect()
                    # Mapping for Deriv-specific intervals
                    deriv_interval = "15 mins" if interval == "15_MINUTE" else "1 hour"
                    await MarketDataService.fetch_historical_ohlcv(
                        client, instrument, bar_size=deriv_interval
                    )
                    await client.disconnect()

            try:
                async_to_sync(sync_flow)()
            except Exception as e:
                logger.error(f"Auto-Sync failed for {symbol}: {e}")

        # 1. Ensure ML model exists (Auto-train requirement)
        model_path = self.ml_service.get_model_path(symbol)
        if not os.path.exists(model_path):
            logger.info(f"Auto-training Quantum model for {symbol}...")
            self.ml_service.train_model(instrument, interval)

        # 2. Load historical bars for simulation
        bars = HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            start_time__range=(start_date, end_date),
        ).order_by("start_time")

        if not bars.exists():
            return {"error": "No historical data found for period"}

        df = pd.DataFrame(
            list(
                bars.values(
                    "start_time",
                    "open_price",
                    "high_price",
                    "low_price",
                    "close_price",
                    "volume",
                )
            )
        )
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        # Simulation Loop
        for i in range(50, len(df)):
            current_bar = df.iloc[i]
            window = df.iloc[i - 50 : i + 1]

            # 1. Update existing positions
            self._update_positions(current_bar)

            # 2. Check for new setups
            if len(self.positions) >= 3:
                continue

            # Detect ICT Signatures (FVG + Sweeps)
            ict_signals = self.ict_service.detect_fvg(
                instrument, interval, df_bars=window.iloc[-3:]
            )
            if not ict_signals:
                ict_signals = self.ict_service.detect_liquidity_sweeps(
                    instrument, interval, df_bars=window
                )

            if ict_signals:
                self.total_setups += 1
                self.confluence_counts["ICT"] += 1

                setup = ict_signals[-1]
                quant_data = self.quant_service.calculate_indicators(window)
                if quant_data["regime"] != "NEUTRAL":
                    self.confluence_counts["Quant"] += 1

                ml_prob = self.ml_service.predict_success(setup, quant_data)
                if ml_prob >= 0.6:
                    self.confluence_counts["ML"] += 1

                # 3. Grade and Audit
                grade_result = self.grading_service.grade_setup(
                    instrument,
                    interval,
                    backtest_setup=setup,
                    backtest_quant=quant_data,
                    backtest_ml_prob=ml_prob,
                )
                grade = grade_result["grade"]

                # Log telemetry for backtest debugging
                if "BACKTEST" in str(getattr(self, "mode", "")):
                    logging.getLogger(__name__).debug(
                        f"[BACKTEST][{symbol}] Setup: {setup['type']} | Grade: {grade} | ML Prob: {ml_prob:.2f}"
                    )

                # Filter out low-volatility "noise" setup in synthetic/random data
                atr = quant_data.get("atr", 0.0)
                mean_close = float(window["close"].mean())
                # Relaxed volatility filter: 0.005% threshold for ultra-quiet synthetic days
                # If atr is naturally 0.0 due to cold starts, we allow it to pass temporarily
                if atr > 0.0 and atr < (mean_close * 0.00005):
                    self.rejected_reasons["VOLATILITY"] += 1
                    self.rejected_setups += 1
                    if getattr(self, "mode", "") == "BACKTEST":
                        logger.debug(
                            f"[BACKTEST][{symbol}] Setup rejected: Low Volatility (ATR: {atr:.6f})"
                        )
                    continue

                # Allow A+, A, B, and C grades (C trades with reduced risk)
                if grade in ["A+", "A", "B", "C"]:
                    # Execute entry
                    risk_check = self.risk_service.validate_trade(
                        None,
                        instrument,
                        grade,
                        Decimal(str(current_bar["close"])),
                        Decimal(str(self.equity)),
                        win_probability=ml_prob,
                    )

                    if risk_check["allowed"]:
                        self._enter_trade(
                            current_bar,
                            setup,
                            risk_check["suggested_quantity"],
                            grade,
                            symbol,
                            window,
                        )
                        if getattr(self, "mode", "") == "BACKTEST":
                            logger.debug(
                                f"[BACKTEST][{symbol}] TRADE EXECUTED: {setup['type']} at {current_bar['close']}"
                            )
                    else:
                        self.rejected_reasons["RISK"] += 1
                        self.rejected_setups += 1
                        if getattr(self, "mode", "") == "BACKTEST":
                            logger.debug(
                                f"[BACKTEST][{symbol}] Setup rejected: RISK ({risk_check.get('reason', 'Unknown')})"
                            )
                else:
                    self.rejected_reasons["GRADE"] += 1
                    self.rejected_setups += 1
                    if getattr(self, "mode", "") == "BACKTEST":
                        logger.debug(
                            f"[BACKTEST][{symbol}] Setup rejected: GRADE ({grade})"
                        )
                    # Harvest rejected Grade D for self-learning
                    try:
                        feat_df = self.ml_service.extract_features(instrument, interval)
                        if feat_df is not None:
                            self.ml_service.harvest_outcome(
                                symbol,
                                feat_df.iloc[-1].to_dict(),
                                "REJECTED",
                                setup_type=setup["type"],
                            )
                    except Exception:
                        pass

            # Update Equity and Peak for Drawdown
            self.peak_equity = max(self.peak_equity, float(self.equity))
            current_dd = (self.peak_equity - float(self.equity)) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, current_dd)

            self.equity_curve.append(
                {
                    "timestamp": str(current_bar["timestamp"]),
                    "equity": float(self.equity),
                }
            )

        return self._get_results(symbol)

    def _enter_trade(self, bar, setup, quantity, grade, symbol="R_25", window=None):
        # ATR-Based Dynamic Risk management
        from decimal import Decimal

        atr = 0
        if window is not None:
            # Calculate 14-period ATR for the current entry point
            high_low = window["high"] - window["low"]
            high_cp = abs(window["high"] - window["close"].shift())
            low_cp = abs(window["low"] - window["close"].shift())
            tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[-1])

        entry_price = float(bar["close"])

        # Adaptive SL/TP: 1.5 ATR for Stop, 3.0 ATR for TP (2.0 RR)
        # If ATR is unavailable (data cold), fall back to 1% / 2% defaults
        if atr > 0:
            sl_dist = atr * 1.5
            tp_dist = atr * 3.0
            tp = entry_price + (setup["direction"] * tp_dist)
            sl = entry_price - (setup["direction"] * sl_dist)
        else:
            tp = entry_price + (setup["direction"] * entry_price * 0.02)
            sl = entry_price - (setup["direction"] * entry_price * 0.01)

        # Size reduction for Grade C trades to "meet in the middle"
        final_qty = quantity if grade != "C" else quantity * Decimal("0.5")

        # Snapshot features for harvesting when trade closes
        features = {}
        if window is not None:
            try:
                # Direct extraction from the current window context for training fidelity
                close_price = float(window["close"].iloc[-1])
                open_price = float(window["open"].iloc[-1])
                high_price = float(window["high"].iloc[-1])
                low_price = float(window["low"].iloc[-1])

                features = {
                    "rsi": float(self.ml_service._calc_rsi(window["close"]).iloc[-1]),
                    "z_score": float(
                        (close_price - window["close"].rolling(20).mean().iloc[-1])
                        / window["close"].rolling(20).std().iloc[-1]
                        if window["close"].rolling(20).std().iloc[-1] != 0
                        else 0
                    ),
                    "atr": float(
                        window["close"].diff().abs().rolling(14).mean().iloc[-1]
                    ),
                    "vol_ratio": float(
                        window["volume"].iloc[-1]
                        / window["volume"].rolling(20).mean().iloc[-1]
                        if window["volume"].rolling(20).mean().iloc[-1] != 0
                        else 1
                    ),
                    "body_size": abs(close_price - open_price),
                    "upper_wick": high_price - max(open_price, close_price),
                    "lower_wick": min(open_price, close_price) - low_price,
                }
            except Exception as e:
                logging.getLogger(__name__).error(f"Feature snapshot failed: {e}")

        self.positions.append(
            {
                "symbol": symbol,
                "type": setup["type"],
                "direction": setup["direction"],
                "entry_price": entry_price,
                "quantity": float(final_qty),
                "tp": tp,
                "sl": sl,
                "grade": grade,
                "features": features,
            }
        )

    def _update_positions(self, bar):
        high = float(bar["high"])
        low = float(bar["low"])

>>>>>>> origin/main
        remaining_positions = []
        for pos in self.positions:
            closed = False
            pnl = 0
<<<<<<< HEAD

            if pos['direction'] == 1: # Long
                if high >= pos['tp']:
                    pnl = (pos['tp'] - pos['entry_price']) * pos['quantity']
                    closed = True
                elif low <= pos['sl']:
                    pnl = (pos['sl'] - pos['entry_price']) * pos['quantity']
                    closed = True
            else: # Short
                if low <= pos['tp']:
                    pnl = (pos['entry_price'] - pos['tp']) * pos['quantity']
                    closed = True
                elif high >= pos['sl']:
                    pnl = (pos['entry_price'] - pos['sl']) * pos['quantity']
                    closed = True

            if closed:
                self.equity += pnl
                self.trades.append({'pnl': pnl, 'grade': pos['grade']})
            else:
                remaining_positions.append(pos)

        self.positions = remaining_positions

    def _get_results(self):
        total_pnl = self.equity - 100000.0
        wins = [t for t in self.trades if t['pnl'] > 0]
        win_rate = (len(wins) / len(self.trades) * 100) if self.trades else 0

        return {
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': len(self.trades),
            'equity_curve': self.equity_curve,
            'final_equity': round(self.equity, 2)
=======

            if pos["direction"] == 1:  # Long
                if high >= pos["tp"]:
                    pnl = (pos["tp"] - pos["entry_price"]) * pos["quantity"]
                    closed = True
                elif low <= pos["sl"]:
                    pnl = (pos["sl"] - pos["entry_price"]) * pos["quantity"]
                    closed = True
            else:  # Short
                if low <= pos["tp"]:
                    pnl = (pos["entry_price"] - pos["tp"]) * pos["quantity"]
                    closed = True
                elif high >= pos["sl"]:
                    pnl = (pos["entry_price"] - pos["sl"]) * pos["quantity"]
                    closed = True

            if closed:
                self.equity += pnl
                self.trades.append({"pnl": pnl, "grade": pos["grade"]})
                # Harvest outcome for Self-Learning
                try:
                    outcome = "WIN" if pnl > 0 else "LOSS"
                    self.ml_service.harvest_outcome(
                        pos["symbol"],
                        pos.get("features", {}),
                        outcome,
                        pnl=float(pnl),
                        setup_type=pos["type"],
                    )
                except Exception as e:
                    logging.getLogger(__name__).error(f"Harvesting failed: {e}")
            else:
                remaining_positions.append(pos)

        self.positions = remaining_positions

    def _get_results(self, symbol="UNKNOWN"):
        total_pnl = float(self.equity) - 100000.0
        wins = [t for t in self.trades if t["pnl"] > 0]
        win_rate = (len(wins) / len(self.trades) * 100) if self.trades else 0

        return {
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": len(self.trades),
            "total_setups": self.total_setups,
            "rejected_setups": self.rejected_setups,
            "equity_curve": self.equity_curve,
            "final_equity": round(float(self.equity), 2),
            "metrics_json": {
                "max_drawdown": round(self.max_drawdown * 100, 2),
                "confluence_breakdown": self.confluence_counts,
                "rejection_reasons": self.rejected_reasons,
                "average_trade_pnl": round(total_pnl / len(self.trades), 2)
                if self.trades
                else 0,
            },
>>>>>>> origin/main
        }
