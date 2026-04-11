<<<<<<< HEAD
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.strategies.services import BacktestService
from apps.tenants.models import Tenant
from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

class Command(BaseCommand):
    help = 'Run a 2-month strategy backtest and show PnL'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default='GBPJPY')
        parser.add_argument('--days', type=int, default=60)

    def handle(self, *args, **options):
        symbol = options['symbol']
        days = options['days']

        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenant found. Run seed_brokers first.'))
            return

        instrument, _ = Instrument.objects.get_or_create(
            symbol=symbol,
            defaults={'name': symbol, 'instrument_type': 'FOREX', 'exchange': 'IDEALPRO', 'currency': 'JPY'}
        )

        # 1. Seed historical data for the backtest period if missing
        self.stdout.write(f"Preparing historical data for {symbol}...")
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        current_time = start_date
        price = 180.00 if 'JPY' in symbol else 50000.0

        bars_to_create = []
        while current_time < end_date:
            # Injecting Intentional ICT Setups every ~50 bars
            is_setup = random.random() < 0.02

            if is_setup:
                # Bullish FVG Sequence
                b1_open, b1_close = price, price * 1.002
                b2_open, b2_close = b1_close, b1_close * 1.01 # BIG BAR
                b3_open, b3_close = b2_close, b2_close * 1.002

=======
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument
from apps.strategies.services import BacktestService


class Command(BaseCommand):
    help = "Run a 2-month strategy backtest and show PnL"

    def add_arguments(self, parser):
        parser.add_argument("--symbol", type=str, default="GBPJPY")
        parser.add_argument("--days", type=int, default=60)

    def handle(self, *args, **options):
        symbol = options["symbol"]
        days = options["days"]

        instrument = Instrument.objects.filter(symbol=symbol).first()
        if not instrument:
            instrument = Instrument.objects.create(
                symbol=symbol,
                name=symbol,
                instrument_type="FOREX"
                if "JPY" in symbol or "USD" in symbol
                else "SYNTHETIC",
                exchange="DERIV"
                if ("R_" in symbol or "JD" in symbol or "BOOM" in symbol)
                else "IDEALPRO",
                currency="USD",
            )

        # 0. Cleanup old data for this instrument to prevent signal pollution
        self.stdout.write(f"Clearing old cache for {symbol}...")
        HistoricalData.objects.filter(instrument=instrument).delete()

        # 1. Seed historical data for the backtest period if missing
        self.stdout.write(f"Preparing stable historical data for {symbol}...")
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        current_time = start_date
        initial_price = 180.00 if "JPY" in symbol else 50000.0
        price = initial_price

        bars_to_create = []
        while current_time < end_date:
            # Injecting Intentional ICT Setups every ~50 bars
            is_setup = random.random() < 0.02  # noqa: S311

            if is_setup:
                # Bullish FVG Sequence
                b1_open, b1_close = price, price * 1.002
                b2_open, b2_close = b1_close, b1_close * 1.01  # BIG BAR
                b3_open, b3_close = b2_close, b2_close * 1.002

>>>>>>> origin/main
                # FVG Condition: b3_low > b1_high
                # Let's make it a significant gap and force OVERSOLD regime prior
                # ICT FVG: Bar 1 High < Bar 3 Low
                b1_open, b1_close = price, price + 2
                b1_high, b1_low = b1_close + 1, b1_open - 1
<<<<<<< HEAD

                b2_open, b2_close = b1_close + 1, b1_close + 20 # Big push
                b2_high, b2_low = b2_close + 1, b2_open - 1

                b3_open, b3_close = b2_close + 1, b2_close + 3
                b3_high, b3_low = b3_close + 1, b1_high + 5 # CLEAR GAP

                seq = [
                    (b1_open, b1_high, b1_low, b1_close),
                    (b2_open, b2_high, b2_low, b2_close),
                    (b3_open, b3_high, b3_low, b3_close)
                ]

                for o, h, l, c in seq:
                    bars_to_create.append(HistoricalData(
                        instrument=instrument, data_type='OHLC', interval='15_MINUTE',
                        start_time=current_time, end_time=current_time + timedelta(minutes=15),
                        open_price=Decimal(str(round(o, 4))), high_price=Decimal(str(round(h, 4))),
                        low_price=Decimal(str(round(l, 4))), close_price=Decimal(str(round(c, 4))),
                        volume=random.randint(500, 2000)
                    ))
=======

                b2_open, b2_close = b1_close + 1, b1_close + 20  # Big push
                b2_high, b2_low = b2_close + 1, b2_open - 1

                b3_open, b3_close = b2_close + 1, b2_close + 3
                b3_high, b3_low = b3_close + 1, b1_high + 5  # CLEAR GAP

                seq = [
                    (b1_open, b1_high, b1_low, b1_close),
                    (b2_open, b2_high, b2_low, b2_close),
                    (b3_open, b3_high, b3_low, b3_close),
                ]

                for o, h, low_val, c in seq:
                    bars_to_create.append(
                        HistoricalData(
                            instrument=instrument,
                            data_type="OHLC",
                            interval="15_MINUTE",
                            start_time=current_time,
                            end_time=current_time + timedelta(minutes=15),
                            open_price=Decimal(str(round(o, 4))),
                            high_price=Decimal(str(round(h, 4))),
                            low_price=Decimal(str(round(low_val, 4))),
                            close_price=Decimal(str(round(c, 4))),
                            volume=random.randint(500, 2000),  # noqa: S311
                        )
                    )
>>>>>>> origin/main
                    current_time += timedelta(minutes=15)
                price = b3_close
                # Next few bars follow through to hit TP
                for _ in range(5):
                    price *= 1.005
<<<<<<< HEAD
                    bars_to_create.append(HistoricalData(
                        instrument=instrument, data_type='OHLC', interval='15_MINUTE',
                        start_time=current_time, end_time=current_time + timedelta(minutes=15),
                        open_price=Decimal(str(round(price/1.005, 4))), high_price=Decimal(str(round(price*1.001, 4))),
                        low_price=Decimal(str(round(price*0.999, 4))), close_price=Decimal(str(round(price, 4))),
                        volume=200
                    ))
                    current_time += timedelta(minutes=15)
            else:
                # Normal random walk
                change = random.uniform(-0.001, 0.001)
                open_p = price
                close_p = price * (1 + change)
                high_p = max(open_p, close_p) + 0.05
                low_p = min(open_p, close_p) - 0.05

                bars_to_create.append(HistoricalData(
                    instrument=instrument, data_type='OHLC', interval='15_MINUTE',
                    start_time=current_time, end_time=current_time + timedelta(minutes=15),
                    open_price=Decimal(str(round(open_p, 4))), high_price=Decimal(str(round(high_p, 4))),
                    low_price=Decimal(str(round(low_p, 4))), close_price=Decimal(str(round(close_p, 4))),
                    volume=random.randint(100, 500)
                ))
                price = close_p
                current_time += timedelta(minutes=15)

            if len(bars_to_create) >= 1000:
                HistoricalData.objects.bulk_create(bars_to_create, ignore_conflicts=True)
                bars_to_create = []

        HistoricalData.objects.bulk_create(bars_to_create, ignore_conflicts=True)

        # 2. Run the Backtest
        self.stdout.write(self.style.SUCCESS(f"Starting Backtest for {symbol} (Last {days} days)..."))
        engine = BacktestService(tenant)
        results = engine.run(symbol, start_date, end_date)

        if "error" in results:
            self.stdout.write(self.style.ERROR(results['error']))
            return

        from apps.strategies.models import BacktestResult
=======
                    bars_to_create.append(
                        HistoricalData(
                            instrument=instrument,
                            data_type="OHLC",
                            interval="15_MINUTE",
                            start_time=current_time,
                            end_time=current_time + timedelta(minutes=15),
                            open_price=Decimal(str(round(price / 1.005, 4))),
                            high_price=Decimal(str(round(price * 1.001, 4))),
                            low_price=Decimal(str(round(price * 0.999, 4))),
                            close_price=Decimal(str(round(price, 4))),
                            volume=200,
                        )
                    )
                    current_time += timedelta(minutes=15)
            else:
                # Stable Mean-Reverting Walk (Ornstein-Uhlenbeck simplified)
                # Helps prevent exponential drift during 365-day runs
                mu = initial_price
                theta = 0.01  # Reversion strength
                sigma = 0.002  # Volatility

                price_change = theta * (mu - price) + price * random.uniform(  # noqa: S311
                    -sigma, sigma
                )
                price += price_change

                # Overflow/Underflow Safety Clamps
                price = max(1.0, min(price, 1000000000.0))

                open_p = price
                close_p = price + (price * random.uniform(-0.0005, 0.0005))  # noqa: S311
                high_p = max(open_p, close_p) + (price * 0.0001)
                low_p = min(open_p, close_p) - (price * 0.0001)

                bars_to_create.append(
                    HistoricalData(
                        instrument=instrument,
                        data_type="OHLC",
                        interval="15_MINUTE",
                        start_time=current_time,
                        end_time=current_time + timedelta(minutes=15),
                        open_price=Decimal(str(round(open_p, 4))),
                        high_price=Decimal(str(round(high_p, 4))),
                        low_price=Decimal(str(round(low_p, 4))),
                        close_price=Decimal(str(round(close_p, 4))),
                        volume=random.randint(100, 500),  # noqa: S311
                    )
                )
                current_time += timedelta(minutes=15)

            if len(bars_to_create) >= 1000:
                HistoricalData.objects.bulk_create(
                    bars_to_create, ignore_conflicts=True
                )
                bars_to_create = []

        HistoricalData.objects.bulk_create(bars_to_create, ignore_conflicts=True)

        # 2. Run the Backtest
        self.stdout.write(
            self.style.SUCCESS(f"Starting Backtest for {symbol} (Last {days} days)...")
        )
        engine = BacktestService()
        results = engine.run(symbol, start_date, end_date)

        if "error" in results:
            self.stdout.write(self.style.ERROR(results["error"]))
            return

        from apps.strategies.models import BacktestResult

>>>>>>> origin/main
        BacktestResult.objects.create(
            instrument=instrument,
            start_date=start_date,
            end_date=end_date,
<<<<<<< HEAD
            total_trades=results['total_trades'],
            win_rate=Decimal(str(results['win_rate'])),
            total_pnl=Decimal(str(results['total_pnl'])),
            final_equity=Decimal(str(results['final_equity'])),
            equity_curve=results['equity_curve']
        )

        # 3. Output results
        self.stdout.write("\n" + "="*40)
        self.stdout.write(f"BACKTEST RESULTS: {symbol}")
        self.stdout.write("="*40)
=======
            total_trades=results["total_trades"],
            win_rate=Decimal(str(results["win_rate"])),
            total_pnl=Decimal(str(results["total_pnl"])),
            final_equity=Decimal(str(results["final_equity"])),
            equity_curve=results["equity_curve"],
        )

        # 3. Output results
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write(f"BACKTEST RESULTS: {symbol}")
        self.stdout.write("=" * 40)
>>>>>>> origin/main
        self.stdout.write(f"Start Date:   {start_date.date()}")
        self.stdout.write(f"End Date:     {end_date.date()}")
        self.stdout.write(f"Total Trades: {results['total_trades']}")
        self.stdout.write(f"Win Rate:     {results['win_rate']}%")
<<<<<<< HEAD

        color_func = self.style.SUCCESS if results['total_pnl'] > 0 else self.style.ERROR
        self.stdout.write(color_func(f"Total PnL:    ${results['total_pnl']}"))
        self.stdout.write(f"Final Equity: ${results['final_equity']}")
        self.stdout.write("="*40 + "\n")
=======

        color_func = (
            self.style.SUCCESS if results["total_pnl"] > 0 else self.style.ERROR
        )
        self.stdout.write(color_func(f"Total PnL:    ${results['total_pnl']}"))
        self.stdout.write(f"Final Equity: ${results['final_equity']}")
        self.stdout.write("=" * 40 + "\n")
>>>>>>> origin/main
