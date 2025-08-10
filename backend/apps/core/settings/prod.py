"""
Production settings for OMS Trading project.

This file contains settings specific to production environment.
Security and performance optimizations are applied here.
"""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403,F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hosts/domain names that are valid for this site
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405

# Database configuration for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),  # noqa: F405
        "USER": env("DB_USER"),  # noqa: F405
        "PASSWORD": env("DB_PASSWORD"),  # noqa: F405
        "HOST": env("DB_HOST"),  # noqa: F405
        "PORT": env("DB_PORT", default="5432"),  # noqa: F405
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": "require",
        },
        "CONN_MAX_AGE": 600,  # 10 minutes connection pooling
    }
}

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = True

# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"

# Additional security headers
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# CORS settings for production
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])  # noqa: F405
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Cache configuration for production
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),  # noqa: F405
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "oms_prod",
        "TIMEOUT": 300,
        "VERSION": 1,
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),  # noqa: F405
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "oms_sessions",
        "TIMEOUT": 86400,  # 1 day
    },
}

# Session backend
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# Email configuration for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")  # noqa: F405
EMAIL_PORT = env("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")  # noqa: F405
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")  # noqa: F405
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)  # noqa: F405

# Static files configuration for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

# Media files configuration for production
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")  # noqa: F405
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")  # noqa: F405
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")  # noqa: F405
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")  # noqa: F405
AWS_DEFAULT_ACL = "private"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600

# Celery configuration for production
CELERY_BROKER_URL = env("CELERY_BROKER_URL")  # noqa: F405
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=env("REDIS_URL"))  # noqa: F405,F405
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 500
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 3600,  # 1 hour
    "fanout_prefix": True,
    "fanout_patterns": True,
}

# Production logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(funcName)s %(lineno)d %(request_id)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 10,
            "formatter": "json",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django_error.log",  # noqa: F405
            "maxBytes": 1024 * 1024 * 100,  # 100 MB
            "backupCount": 10,
            "formatter": "json",
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "security.log",  # noqa: F405
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 20,
            "formatter": "json",
        },
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"],
    },
    "loggers": {
        "django": {
            "handlers": ["file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "ib_insync": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "gunicorn": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Sentry configuration for production
SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling_integrations=False),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.01,  # 1% sampling for performance
        send_default_pii=False,
        environment="production",
        release=env("RELEASE_VERSION", default="latest"),  # noqa: F405
        before_send=lambda event, hint: event if event.get("level") != "info" else None,
    )

# Interactive Brokers configuration for production
IB_CONFIG.update({  # noqa: F405
    "HOST": env("IB_HOST"),  # noqa: F405
    "PORT": env("IB_PORT"),  # noqa: F405
    "CLIENT_ID": env("IB_CLIENT_ID"),  # noqa: F405
    "READONLY": env("IB_READONLY", default=False),  # noqa: F405
    "ACCOUNT": env("IB_ACCOUNT"),  # noqa: F405
    "TIMEOUT": 60,
    "RECONNECT_ATTEMPTS": 10,
    "RECONNECT_DELAY": 30,
})

# Risk management configuration for production
RISK_CONFIG.update({  # noqa: F405
    "MAX_POSITION_SIZE": env("RISK_MAX_POSITION_SIZE", default=1000000),  # noqa: F405
    "MAX_ORDER_SIZE": env("RISK_MAX_ORDER_SIZE", default=100000),  # noqa: F405
    "MAX_DAILY_LOSS": env("RISK_MAX_DAILY_LOSS", default=50000),  # noqa: F405
    "MAX_ORDERS_PER_MINUTE": env("RISK_MAX_ORDERS_PER_MINUTE", default=60),  # noqa: F405
    "ENABLE_PRE_TRADE_CHECKS": True,
    "ENABLE_POSITION_LIMITS": True,
})

# Strategy configuration for production
STRATEGY_CONFIG.update({  # noqa: F405
    "MAX_CONCURRENT_RUNS": env("STRATEGY_MAX_CONCURRENT_RUNS", default=10),  # noqa: F405
    "DEFAULT_TIMEOUT": env("STRATEGY_DEFAULT_TIMEOUT", default=3600),  # noqa: F405
    "ENABLE_SANDBOXING": True,
    "PAPER_TRADING_ONLY": env("STRATEGY_PAPER_TRADING_ONLY", default=False),  # noqa: F405
    "LOG_RETENTION_DAYS": 90,
})

# Rate limiting for production
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# Database connection pool settings
DATABASES["default"]["OPTIONS"].update({
    "MAX_CONNS": 20,
    "MIN_CONNS": 5,
})

# Template caching
for template in TEMPLATES:  # noqa: F405
    template["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

# Admin security
ADMIN_URL = env("ADMIN_URL", default="admin/")  # noqa: F405
ADMINS = [
    (name, email) for name, email in 
    [admin.split(":") for admin in env.list("ADMINS", default=[])]  # noqa: F405
]
MANAGERS = ADMINS

# File upload limits for production
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB

# Time zone for production
TIME_ZONE = env("TIME_ZONE", default="America/New_York")  # noqa: F405

# Performance optimizations
CONN_MAX_AGE = 600  # 10 minutes

# Disable browsable API in production
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Additional middleware for production
MIDDLEWARE = [  # noqa: F405
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
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.AuditLogMiddleware",
    "apps.tenants.middleware.TenantMiddleware",
    "apps.core.middleware.RateLimitMiddleware",
]

# Monitoring and health checks
HEALTH_CHECK_ENDPOINTS = [
    "/health/",
    "/health/ready/",
    "/health/live/",
]

# Force HTTPS URLs
USE_TLS = True

# Password validation for production
AUTH_PASSWORD_VALIDATORS += [  # noqa: F405
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        }
    },
]

print("🔒 Running in PRODUCTION mode")  # noqa: T201
