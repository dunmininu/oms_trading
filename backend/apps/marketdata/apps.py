"""
Market Data app configuration.
"""

from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    """Configuration for the market data app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.marketdata'
    verbose_name = 'Market Data'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.marketdata.signals  # noqa: F401
        except ImportError:
            pass
