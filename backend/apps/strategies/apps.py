"""
Strategies app configuration.
"""

from django.apps import AppConfig


class StrategiesConfig(AppConfig):
    """Configuration for the strategies app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.strategies'
    verbose_name = 'Trading Strategies'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.strategies.signals  # noqa: F401
        except ImportError:
            pass
