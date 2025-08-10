"""
Base Django settings for OMS Trading project.

This file contains common settings for all environments.
For environment-specific settings, see dev.py, prod.py, and test.py.
"""

import os
import sys
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
APPS_DIR = BACKEND_DIR / "apps"

# Environment variables
env = environ.Env(
    # Set casting and default values
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, ""),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, ""),
    SENTRY_DSN=(str, ""),
    IB_HOST=(str, "127.0.0.1"),
    IB_PORT=(int, 7497),
    IB_CLIENT_ID=(int, 1),
    JWT_SECRET_KEY=(str, ""),
    API_KEY_SECRET=(str, ""),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / ".env")

# Add apps directory to Python path
sys.path.insert(0, str(APPS_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_extensions",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.tenants", 
    "apps.brokers",
    "apps.marketdata",
    "apps.oms",
    "apps.strategies",
    "apps.events",
    "apps.api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "apps.core.middleware.RequestIDMiddleware",
    "apps.core.middleware.AuditLogMiddleware",
    "apps.tenants.middleware.TenantMiddleware",
]

ROOT_URLCONF = "apps.api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BACKEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "apps.core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BACKEND_DIR / "static",
]

# Static files storage
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "oms",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Session configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.JWTAuthentication",
        "apps.accounts.authentication.APIKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "DATE_FORMAT": "%Y-%m-%d",
    "TIME_FORMAT": "%H:%M:%S",
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue development server
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Celery Configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=env("REDIS_URL"))
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 5  # 5 minutes
CELERY_TASK_TIME_LIMIT = 60 * 10  # 10 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "reconcile-positions": {
        "task": "apps.oms.tasks.reconcile_positions",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-idempotency-keys": {
        "task": "apps.core.tasks.cleanup_idempotency_keys",
        "schedule": 3600.0,  # Every hour
    },
    "daily-pnl-snapshot": {
        "task": "apps.oms.tasks.create_daily_pnl_snapshot",
        "schedule": {
            "hour": 18,  # 6 PM EST (after market close)
            "minute": 0,
        },
    },
}

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(funcName)s %(lineno)d",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 5,
            "formatter": "json",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django_error.log",
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "ib_insync": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / "logs").mkdir(exist_ok=True)

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = env("JWT_SECRET_KEY", default=SECRET_KEY)
JWT_ACCESS_TOKEN_LIFETIME = 900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME = 604800  # 7 days
JWT_ROTATE_REFRESH_TOKENS = True
JWT_BLACKLIST_AFTER_ROTATION = True

# API Key Configuration
API_KEY_SECRET = env("API_KEY_SECRET", default=SECRET_KEY)
API_KEY_HEADER_NAME = "X-API-Key"
API_KEY_PREFIX = "oms_"

# Interactive Brokers Configuration
IB_CONFIG = {
    "HOST": env("IB_HOST"),
    "PORT": env("IB_PORT"),
    "CLIENT_ID": env("IB_CLIENT_ID"),
    "TIMEOUT": 30,
    "READONLY": False,  # Set to True for paper trading
    "ACCOUNT": env("IB_ACCOUNT", default=""),
    "RECONNECT_ATTEMPTS": 5,
    "RECONNECT_DELAY": 5,
}

# Risk Management Configuration
RISK_CONFIG = {
    "MAX_POSITION_SIZE": 1000000,  # $1M default
    "MAX_ORDER_SIZE": 100000,     # $100K default
    "MAX_DAILY_LOSS": 50000,      # $50K default
    "MAX_ORDERS_PER_MINUTE": 60,
    "ENABLE_PRE_TRADE_CHECKS": True,
    "ENABLE_POSITION_LIMITS": True,
}

# Market Data Configuration
MARKET_DATA_CONFIG = {
    "CACHE_TIMEOUT": 60,  # 1 minute
    "SNAPSHOT_INTERVAL": 300,  # 5 minutes
    "ENABLE_TICK_STORAGE": False,  # Disable for performance
    "MAX_SUBSCRIPTIONS_PER_TENANT": 100,
}

# Strategy Configuration
STRATEGY_CONFIG = {
    "MAX_CONCURRENT_RUNS": 5,
    "DEFAULT_TIMEOUT": 3600,  # 1 hour
    "ENABLE_SANDBOXING": True,
    "PAPER_TRADING_ONLY": True,  # Safety default
    "LOG_RETENTION_DAYS": 30,
}

# Webhook Configuration
WEBHOOK_CONFIG = {
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 60,  # 1 minute
    "TIMEOUT": 30,  # 30 seconds
    "SIGNATURE_HEADER": "X-OMS-Signature",
    "USER_AGENT": "OMS-Trading-Webhook/1.0",
}

# Rate Limiting Configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# Audit Log Configuration
AUDIT_LOG_ENABLED = True
AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years for compliance

# File Upload Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Email Configuration (for notifications)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@omstrading.com")

# Sentry Configuration
SENTRY_DSN = env("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling_integrations=False),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env("ENVIRONMENT", default="development"),
    )
