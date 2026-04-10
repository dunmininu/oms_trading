"""
Market data services for ingestion and caching.
"""

import logging
from datetime import timedelta
from typing import Any

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument
from libs.ibsdk.contracts import create_btcusd_contract, create_gbpjpy_contract

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for managing market data ingestion."""

    @classmethod
    async def ensure_instruments(cls):
        """Ensure required instruments (GBPJPY, BTCUSD) exist in the database."""
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

    @classmethod
    async def fetch_historical_ohlcv(
        cls,
        client: Any,
        instrument: Instrument,
        duration: str = "2 D",
        bar_size: str = "15 mins",
    ):
        """Fetch historical OHLCV data from IB and store it."""
        if instrument.symbol == "GBPJPY":
            contract = create_gbpjpy_contract()
        elif instrument.symbol == "BTCUSD" or instrument.symbol == "BTC":
            contract = create_btcusd_contract()
        else:
            logger.error(
                f"Unsupported instrument for historical data: {instrument.symbol}"
            )
            return

        await client.get_contract_details(contract)

        interval_map = {
            "15 mins": "15_MINUTE",
            "4 hours": "4_HOUR",
            "1 min": "1_MINUTE",
            "1 day": "1_DAY",
        }
        interval = interval_map.get(bar_size, "15_MINUTE")

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

        # Use bulk_create for better scalability
        existing_times = set(
            HistoricalData.objects.filter(
                instrument=instrument, interval=interval, data_type="OHLC"
            ).values_list("start_time", flat=True)
        )

        new_bars = []
        for bar in bars:
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

        logger.info(f"Stored {len(bars)} bars for {instrument.symbol} ({interval})")
