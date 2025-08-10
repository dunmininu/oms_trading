"""
Test settings for OMS Trading project.

This file contains settings specific to testing environment.
Optimized for speed and isolation.
"""

from .base import *  # noqa: F403,F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Use in-memory database for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# Disable migrations for tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use in-memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Disable Celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Password hashing for tests (faster)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": False,
        },
        "apps": {
            "handlers": ["null"],
            "propagate": False,
        },
        "celery": {
            "handlers": ["null"],
            "propagate": False,
        },
        "ib_insync": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# Disable Sentry in tests
SENTRY_DSN = ""

# Test-specific IB configuration
IB_CONFIG.update({  # noqa: F405
    "HOST": "127.0.0.1",
    "PORT": 7497,
    "CLIENT_ID": 999,  # Test client ID
    "READONLY": True,
    "ACCOUNT": "TEST123456",
    "TIMEOUT": 5,
    "RECONNECT_ATTEMPTS": 1,
    "RECONNECT_DELAY": 1,
})

# Risk management for tests
RISK_CONFIG.update({  # noqa: F405
    "MAX_POSITION_SIZE": 1000,
    "MAX_ORDER_SIZE": 100,
    "MAX_DAILY_LOSS": 50,
    "MAX_ORDERS_PER_MINUTE": 100,
    "ENABLE_PRE_TRADE_CHECKS": True,
    "ENABLE_POSITION_LIMITS": True,
})

# Strategy configuration for tests
STRATEGY_CONFIG.update({  # noqa: F405
    "MAX_CONCURRENT_RUNS": 1,
    "DEFAULT_TIMEOUT": 30,
    "ENABLE_SANDBOXING": False,
    "PAPER_TRADING_ONLY": True,
    "LOG_RETENTION_DAYS": 1,
})

# Webhook configuration for tests
WEBHOOK_CONFIG.update({  # noqa: F405
    "MAX_RETRIES": 1,
    "RETRY_DELAY": 1,
    "TIMEOUT": 5,
})

# Market data configuration for tests
MARKET_DATA_CONFIG.update({  # noqa: F405
    "CACHE_TIMEOUT": 10,
    "SNAPSHOT_INTERVAL": 30,
    "ENABLE_TICK_STORAGE": False,
    "MAX_SUBSCRIPTIONS_PER_TENANT": 10,
})

# Security settings for tests
SECRET_KEY = "test-secret-key-not-for-production"
JWT_SECRET_KEY = "test-jwt-secret-key"
API_KEY_SECRET = "test-api-key-secret"

# Disable security features for tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Disable rate limiting for tests
RATELIMIT_ENABLE = False

# Audit log configuration for tests
AUDIT_LOG_ENABLED = False

# File upload settings for tests
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1 MB

# Media files for tests
MEDIA_ROOT = "/tmp/oms_test_media"  # noqa: S108

# Static files for tests
STATIC_ROOT = "/tmp/oms_test_static"  # noqa: S108

# Time zone for tests
TIME_ZONE = "UTC"
USE_TZ = True

# Internationalization for tests
USE_I18N = False
USE_L10N = False

# Test-specific middleware (minimal)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.core.middleware.RequestIDMiddleware",
    "apps.tenants.middleware.TenantMiddleware",
]

# Remove debug toolbar from test apps
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa: F405

# JWT configuration for tests
JWT_ACCESS_TOKEN_LIFETIME = 60  # 1 minute
JWT_REFRESH_TOKEN_LIFETIME = 300  # 5 minutes

# Test database settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"
TEST_NON_SERIALIZED_APPS = []

# Allow all hosts in tests
ALLOWED_HOSTS = ["*"]

# CORS settings for tests
CORS_ALLOW_ALL_ORIGINS = True

print("🧪 Running in TEST mode")  # noqa: T201
