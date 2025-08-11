"""
System and health check API endpoints.
"""

from ninja import Router
from typing import List, Dict, Any
from django.http import HttpRequest
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import platform
import time

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None

router = Router()


@router.get("/health", tags=["System"])
def health_check(request: HttpRequest) -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "OMS Trading API",
        "version": "1.0.0",
        "timestamp": time.time(),
        "environment": getattr(settings, 'DJANGO_SETTINGS_MODULE', 'unknown')
    }


@router.get("/health/ready", tags=["System"])
def health_ready(request: HttpRequest) -> Dict[str, Any]:
    """Readiness probe endpoint for Kubernetes/load balancers."""
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


@router.get("/version", tags=["System"])
def version_info(request: HttpRequest) -> Dict[str, Any]:
    """Get detailed version information."""
    return {
        "service": "OMS Trading API",
        "version": "1.0.0",
        "build_date": "2024-01-01T00:00:00Z",  # TODO: Get from build info
        "git_commit": "unknown",  # TODO: Get from git
        "python_version": platform.python_version(),
        "django_version": "5.1.11",
        "environment": getattr(settings, 'DJANGO_SETTINGS_MODULE', 'unknown')
    }


@router.get("/info", tags=["System"])
def system_info(request: HttpRequest) -> Dict[str, Any]:
    """Get system information."""
    return {
        "system": "OMS Trading",
        "version": "1.0.0",
        "status": "operational",
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation()
    }


@router.get("/metrics", tags=["System"])
def system_metrics(request: HttpRequest) -> Dict[str, Any]:
    """Get system metrics."""
    try:
        if psutil is None:
            return {
                "warning": "psutil not installed; returning minimal metrics",
                "timestamp": time.time(),
            }

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time(),
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        return {
            "error": "Failed to collect metrics",
            "message": str(e),
            "timestamp": time.time()
        }
