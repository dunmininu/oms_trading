"""
Django app configuration for tenants app.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TenantsConfig(AppConfig):
    """Configuration for the tenants app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    verbose_name = _('Tenants')
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.tenants.signals  # noqa
        except ImportError:
            pass
