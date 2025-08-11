"""
Brokers app configuration.
"""

from django.apps import AppConfig


class BrokersConfig(AppConfig):
    """Configuration for the brokers app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.brokers'
    verbose_name = 'Brokers'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.brokers.signals  # noqa: F401
        except ImportError:
            pass
