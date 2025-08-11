"""
OMS app configuration.
"""

from django.apps import AppConfig


class OmsConfig(AppConfig):
    """Configuration for the OMS app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.oms'
    verbose_name = 'Order Management System'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.oms.signals  # noqa: F401
        except ImportError:
            pass
