<<<<<<< HEAD
"""
Market data services for ingestion and caching.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Any
from django.utils import timezone
from django.db import transaction

from apps.oms.models import Instrument
from apps.marketdata.models import HistoricalData, MarketSubscription
from libs.ibsdk.client import IBClient
from libs.ibsdk.contracts import create_gbpjpy_contract, create_btcusd_contract

logger = logging.getLogger(__name__)

=======
import logging
from datetime import timedelta
from typing import Any

from asgiref.sync import sync_to_async

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument
from libs.ibsdk.contracts import create_btcusd_contract, create_gbpjpy_contract

logger = logging.getLogger(__name__)


>>>>>>> origin/main
class MarketDataService:
    """Service for managing market data ingestion."""

    @classmethod
    async def ensure_instruments(cls):
        """Ensure required instruments (GBPJPY, BTCUSD) exist in the database."""
<<<<<<< HEAD
        gbpjpy, created = Instrument.objects.update_or_create(
            symbol='GBPJPY',
            defaults={
                'name': 'GBP/JPY Forex',
                'instrument_type': 'FOREX',
                'exchange': 'IB_SMART',
                'sec_type': 'CASH',
                'currency': 'JPY',
                'is_active': True,
                'is_tradable': True,
            }
        )
        if created:
            logger.info("Created Instrument: GBPJPY")

        btcusd, created = Instrument.objects.update_or_create(
            symbol='BTCUSD',
            defaults={
                'name': 'Bitcoin/USD Crypto',
                'instrument_type': 'CRYPTO',
                'exchange': 'IB_CRYPTO',
                'sec_type': 'CRYPTO',
                'currency': 'USD',
                'is_active': True,
                'is_tradable': True,
            }
        )
        if created:
            logger.info("Created Instrument: BTCUSD")

        return gbpjpy, btcusd

    @classmethod
    async def fetch_historical_ohlcv(
        cls,
        client: Any,
        instrument: Instrument,
        duration: str = '2 D',
        bar_size: str = '15 mins'
    ):
        """Fetch historical OHLCV data from IB and store it."""
        if instrument.symbol == 'GBPJPY':
            contract = create_gbpjpy_contract()
        elif instrument.symbol == 'BTCUSD' or instrument.symbol == 'BTC':
            contract = create_btcusd_contract()
        else:
            logger.error(f"Unsupported instrument for historical data: {instrument.symbol}")
            return

        await client.get_contract_details(contract)

        interval_map = {
            '15 mins': '15_MINUTE',
            '4 hours': '4_HOUR',
            '1 min': '1_MINUTE',
            '1 day': '1_DAY'
        }
        interval = interval_map.get(bar_size, '15_MINUTE')

        bars = await client.req_historical_data(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='MIDPOINT' if instrument.instrument_type == 'FOREX' else 'TRADES',
            useRTH=True
        )

        # Use bulk_create for better scalability
        existing_times = set(HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).values_list('start_time', flat=True))

        new_bars = []
        for bar in bars:
            if bar.date not in existing_times:
                new_bars.append(HistoricalData(
                    instrument=instrument,
                    data_type='OHLC',
                    interval=interval,
                    start_time=bar.date,
                    end_time=bar.date + timedelta(minutes=15) if interval == '15_MINUTE' else bar.date + timedelta(hours=4),
                    open_price=bar.open,
                    high_price=bar.high,
                    low_price=bar.low,
                    close_price=bar.close,
                    volume=bar.volume if bar.volume > 0 else 0,
                ))

        if new_bars:
            HistoricalData.objects.bulk_create(new_bars, batch_size=500)

        logger.info(f"Stored {len(bars)} bars for {instrument.symbol} ({interval})")
=======

        @sync_to_async
        def _ensure():
            gbpjpy, created = Instrument.objects.update_or_create(
                symbol="GBPJPY",
                defaults={
                    "name": "GBP/JPY Forex",
                    "instrument_type": "FOREX",
                    "exchange": "IB_SMART",
                    "sec_type": "CASH",
                    "currency": "JPY",
                    "is_active": True,
                    "is_tradable": True,
                },
            )
            if created:
                logger.info("Created Instrument: GBPJPY")

            btcusd, created = Instrument.objects.update_or_create(
                symbol="BTCUSD",
                defaults={
                    "name": "Bitcoin/USD Crypto",
                    "instrument_type": "CRYPTO",
                    "exchange": "IB_CRYPTO",
                    "sec_type": "CRYPTO",
                    "currency": "USD",
                    "is_active": True,
                    "is_tradable": True,
                },
            )
            if created:
                logger.info("Created Instrument: BTCUSD")
            return gbpjpy, btcusd

        return await _ensure()

    @classmethod
    async def sync_deriv_instruments(cls, client: Any):
        """Fetch all active symbols from Deriv and register them in OMS."""
        from libs.derivsdk.client import DerivClient

        if not isinstance(client, DerivClient):
            return

        symbols = await client.get_active_symbols()

        @sync_to_async
        def _sync(symbol_data):
            new_instruments = 0
            for data in symbol_data:
                # Upsert into Instrument
                inst, created = Instrument.objects.update_or_create(
                    symbol=data["symbol"],
                    defaults={
                        "name": data.get("display_name", data["symbol"]),
                        "instrument_type": "OTHER",
                        "exchange": "DERIV",
                        "sec_type": data.get("submarket", "N/A"),
                        "is_active": True,
                        "is_tradable": True,
                    },
                )
                if created:
                    new_instruments += 1
            return new_instruments

        new_count = await _sync(symbols)
        logger.info(f"Synced {len(symbols)} Deriv active symbols. ({new_count} new)")
        return symbols

    @classmethod
    async def fetch_historical_ohlcv(
        cls,
        client: Any,
        instrument: Instrument,
        duration: str = "2 D",
        bar_size: str = "15 mins",
    ):
        """Fetch historical OHLCV data from Broker and store it."""
        import datetime

        from libs.derivsdk.client import DerivClient

        interval_map = {
            "15 mins": "15_MINUTE",
            "4 hours": "4_HOUR",
            "1 min": "1_MINUTE",
            "1 day": "1_DAY",
        }
        interval = interval_map.get(bar_size, "15_MINUTE")

        if isinstance(client, DerivClient):
            granularity = 900 if interval == "15_MINUTE" else 60
            candles = await client.get_historical_candles(
                instrument.symbol, count=1000, granularity=granularity
            )

            @sync_to_async
            def _store_deriv_candles(candle_data):
                existing_times = set(
                    HistoricalData.objects.filter(
                        instrument=instrument, interval=interval, data_type="OHLC"
                    ).values_list("start_time", flat=True)
                )

                new_bars = []
                for candle in candle_data:
                    dt = datetime.datetime.fromtimestamp(
                        candle["epoch"], tz=datetime.UTC
                    )
                    if dt not in existing_times:
                        new_bars.append(
                            HistoricalData(
                                instrument=instrument,
                                data_type="OHLC",
                                interval=interval,
                                start_time=dt,
                                end_time=dt + timedelta(minutes=15)
                                if interval == "15_MINUTE"
                                else dt + timedelta(hours=4),
                                open_price=candle["open"],
                                high_price=candle["high"],
                                low_price=candle["low"],
                                close_price=candle["close"],
                                volume=0,
                            )
                        )
                if new_bars:
                    HistoricalData.objects.bulk_create(new_bars, batch_size=500)
                return len(new_bars)

            stashed = await _store_deriv_candles(candles)
            logger.info(f"Stored {stashed} new derivation bars for {instrument.symbol}")
            return

        # IB Route
        if instrument.symbol == "GBPJPY":
            contract = create_gbpjpy_contract()
        elif instrument.symbol == "BTCUSD" or instrument.symbol == "BTC":
            contract = create_btcusd_contract()
        else:
            logger.error(
                f"Unsupported IB instrument for historical data: {instrument.symbol}"
            )
            return

        await client.get_contract_details(contract)

        bars = await client.req_historical_data(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=(
                "MIDPOINT" if instrument.instrument_type == "FOREX" else "TRADES"
            ),
            useRTH=True,
        )

        @sync_to_async
        def _store_ib_bars(bar_data):
            existing_times = set(
                HistoricalData.objects.filter(
                    instrument=instrument, interval=interval, data_type="OHLC"
                ).values_list("start_time", flat=True)
            )

            new_bars = []
            for bar in bar_data:
                if bar.date not in existing_times:
                    new_bars.append(
                        HistoricalData(
                            instrument=instrument,
                            data_type="OHLC",
                            interval=interval,
                            start_time=bar.date,
                            end_time=(
                                bar.date + timedelta(minutes=15)
                                if interval == "15_MINUTE"
                                else bar.date + timedelta(hours=4)
                            ),
                            open_price=bar.open,
                            high_price=bar.high,
                            low_price=bar.low,
                            close_price=bar.close,
                            volume=bar.volume if bar.volume > 0 else 0,
                        )
                    )

            if new_bars:
                HistoricalData.objects.bulk_create(new_bars, batch_size=500)
            return len(new_bars)

        stashed = await _store_ib_bars(bars)
        logger.info(
            f"Stored {stashed} new IB bars for {instrument.symbol} ({interval})"
        )
>>>>>>> origin/main
