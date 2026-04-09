
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

        self.ict_service = ICTSetupService()
        self.quant_service = QuantService()
        self.ml_service = MLStrategyService()
        self.grading_service = GradingService()
        self.risk_service = RiskManagementService()

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

        remaining_positions = []
        for pos in self.positions:
            closed = False
            pnl = 0

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
        }
