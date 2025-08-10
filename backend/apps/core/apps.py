"""
Django app configuration for core app.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.core'
    verbose_name = _('Core')
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import backend.apps.core.signals  # noqa
        except ImportError:
            pass
