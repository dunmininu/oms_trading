"""
Development settings for OMS Trading project.

This file contains settings specific to development environment.
"""

from .base import *  # noqa: F403,F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Development-specific apps
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
    "debug_toolbar",
]

# Development middleware
MIDDLEWARE += [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Debug toolbar configuration
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,  # noqa: F405
    "SHOW_TEMPLATE_CONTEXT": True,
    "ENABLE_STACKTRACES": True,
}

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

# Database configuration for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="oms_trading_dev"),  # noqa: F405
        "USER": env("DB_USER", default="postgres"),  # noqa: F405
        "PASSWORD": env("DB_PASSWORD", default="postgres"),  # noqa: F405
        "HOST": env("DB_HOST", default="localhost"),  # noqa: F405
        "PORT": env("DB_PORT", default="5432"),  # noqa: F405
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "CONN_MAX_AGE": 0,  # Disable connection pooling in development
    }
}

# Enable database query logging in development
if DEBUG:
    LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
        "level": "DEBUG",
        "handlers": ["console"],
        "propagate": False,
    }

# Email backend for development (console output)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Security settings for development
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Cache settings for development
CACHES["default"]["LOCATION"] = env("REDIS_URL", default="redis://localhost:6379/0")  # noqa: F405

# Celery settings for development
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")  # noqa: F405
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/1")  # noqa: F405

# Interactive Brokers settings for development
IB_CONFIG.update({  # noqa: F405
    "HOST": env("IB_HOST", default="127.0.0.1"),  # noqa: F405
    "PORT": env("IB_PORT", default=7497),  # noqa: F405 # TWS paper trading port
    "CLIENT_ID": env("IB_CLIENT_ID", default=1),  # noqa: F405
    "READONLY": True,  # Paper trading mode
    "ACCOUNT": env("IB_ACCOUNT", default="DU123456"),  # noqa: F405 # Paper account
})

# Risk management - more lenient for development
RISK_CONFIG.update({  # noqa: F405
    "MAX_POSITION_SIZE": 10000,  # $10K for development
    "MAX_ORDER_SIZE": 1000,     # $1K for development
    "MAX_DAILY_LOSS": 500,      # $500 for development
    "MAX_ORDERS_PER_MINUTE": 10,
})

# Strategy configuration for development
STRATEGY_CONFIG.update({  # noqa: F405
    "PAPER_TRADING_ONLY": True,  # Force paper trading in development
    "ENABLE_SANDBOXING": False,  # Disable for easier debugging
    "MAX_CONCURRENT_RUNS": 2,
})

# Development-specific logging
LOGGING["handlers"]["console"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["ib_insync"]["level"] = "INFO"  # noqa: F405

# Django Extensions configuration
SHELL_PLUS_SETTINGS = {
    "SHELL_PLUS_PRINT_SQL": True,
    "SHELL_PLUS_PRINT_SQL_TRUNCATE": 1000,
}

# Use IPython for shell_plus
SHELL_PLUS = "ipython"

# Internal IPs for debug toolbar
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
]

# Media files served by Django in development
if DEBUG:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# Disable template caching in development
for template in TEMPLATES:  # noqa: F405
    template["OPTIONS"]["debug"] = True

# Console output for development
CONSOLE_LOGGING = True

# Additional development settings
USE_TZ = True
USE_I18N = True
USE_L10N = True

# File upload settings for development
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB

# Development secrets (should be overridden in .env)
if not env("SECRET_KEY", default=""):  # noqa: F405
    SECRET_KEY = "dev-secret-key-change-me-in-production"  # noqa: F405

if not env("JWT_SECRET_KEY", default=""):  # noqa: F405
    JWT_SECRET_KEY = "dev-jwt-secret-key-change-me"  # noqa: F405

if not env("API_KEY_SECRET", default=""):  # noqa: F405
    API_KEY_SECRET = "dev-api-key-secret-change-me"  # noqa: F405

# Faster password hashing for development
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable migration checks in development
MIGRATION_MODULES = {}

print("🚀 Running in DEVELOPMENT mode")  # noqa: T201
