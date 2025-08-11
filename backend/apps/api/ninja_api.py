"""
Main Django Ninja API configuration.
"""

from ninja import NinjaAPI
from ninja.security import HttpBearer
from django.conf import settings
from django.http import HttpRequest
from typing import Optional
import time

from .middleware import TenantMiddleware, RateLimitMiddleware
from .exceptions import APIExceptionHandler
from .schemas import ErrorResponse
from .v1.auth import AuthBearer


# Main API instance
api = NinjaAPI(
    title="OMS Trading API",
    version="1.0.0",
    description="Production-grade Order Management System API",
    auth=AuthBearer(),
    docs_url="/docs",
    openapi_url="/openapi.json",
    urls_namespace="api",
    csrf=False,  # API doesn't need CSRF
)

# Add custom exception handler
api.add_exception_handler(Exception, APIExceptionHandler.handle_exception)

# Note: Django Ninja doesn't support add_middleware like Django
# Middleware is handled at the Django level in settings.py
# TenantMiddleware and RateLimitMiddleware are configured in Django settings

# Include app-specific API routes
from .v1 import auth, tenants, brokers, marketdata, oms, strategies, events, system

# Register v1 API routes
api.add_router("/v1/auth/", auth.router, tags=["Authentication"])
api.add_router("/v1/tenants/", tenants.router, tags=["Tenant Management"])
api.add_router("/v1/brokers/", brokers.router, tags=["Broker Integration"])
api.add_router("/v1/marketdata/", marketdata.router, tags=["Market Data"])
api.add_router("/v1/oms/", oms.router, tags=["Order Management"])
api.add_router("/v1/strategies/", strategies.router, tags=["Strategy Management"])
api.add_router("/v1/events/", events.router, tags=["Events & Webhooks"])
api.add_router("/v1/system/", system.router, tags=["System & Health"])


# Health check endpoint
@api.get("/health", tags=["System"])
def health_check(request):
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "OMS Trading API"}


@api.get("/health/ready", tags=["System"])
def health_ready(request):
    """Readiness probe endpoint for Kubernetes/load balancers."""
    from django.db import connection
    from django.core.cache import cache
    
    checks = {
        "database": False,
        "cache": False,
        "overall": False
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks["database"] = True
    except Exception:
        checks["database"] = False
    
    # Check cache connectivity
    try:
        cache.set("health_check", "ok", 10)
        cache.get("health_check")
        checks["cache"] = True
    except Exception:
        checks["cache"] = False
    
    # Overall health
    checks["overall"] = all([checks["database"], checks["cache"]])
    
    status = "ready" if checks["overall"] else "not_ready"
    
    return {
        "status": status,
        "service": "OMS Trading API",
        "timestamp": time.time(),
        "checks": checks
    }


@api.get("/version", tags=["System"])
def version_info(request):
    """Get detailed version information."""
    import platform
    
    return {
        "service": "OMS Trading API",
        "version": "1.0.0",
        "build_date": "2024-01-01T00:00:00Z",  # TODO: Get from build info
        "git_commit": "unknown",  # TODO: Get from git
        "python_version": platform.python_version(),
        "django_version": "5.1.11",
        "environment": getattr(settings, 'DJANGO_SETTINGS_MODULE', 'unknown')
    }


# Root endpoint
@api.get("/", tags=["System"])
def root(request):
    """API root endpoint."""
    return {
        "service": "OMS Trading API",
        "version": "1.0.0",
        "documentation": "/docs",
        "openapi": "/openapi.json"
    }
