"""
API exception handling for Django Ninja.
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


class APIExceptionHandler:
    """Centralized exception handling for API endpoints."""

    @staticmethod
    def handle_exception(request: HttpRequest, exc: Exception) -> Any:
        """Handle exceptions and return consistent error responses."""
        from django.http import JsonResponse

        # Log the exception
        logger.error(
            f"API Exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_path": request.path,
                "request_method": request.method,
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.META.get("REMOTE_ADDR", ""),
            },
            exc_info=True,
        )

        # Handle specific exception types
        data = {"error": {}}
        status_code = 500

        if isinstance(exc, APIError):
            status_code = exc.code
            data = {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "type": exc.error_type,
                }
            }
            if isinstance(exc, ValidationAPIError) and exc.details:
                data["error"]["details"] = exc.details

        elif isinstance(exc, HttpError):
            status_code = exc.status_code
            data = {
                "error": {
                    "code": exc.status_code,
                    "message": str(exc),
                    "type": "http_error",
                }
            }

        elif isinstance(exc, ValidationError):
            status_code = 400
            data = {
                "error": {
                    "code": 400,
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": (
                        exc.message_dict if hasattr(exc, "message_dict") else str(exc)
                    ),
                }
            }

        elif isinstance(exc, PermissionDenied):
            status_code = 403
            data = {
                "error": {
                    "code": 403,
                    "message": "Permission denied",
                    "type": "permission_error",
                }
            }

        elif isinstance(exc, ValueError):
            status_code = 400
            data = {"error": {"code": 400, "message": str(exc), "type": "value_error"}}

        else:
            # Handle unexpected exceptions
            # In production, don't expose internal error details
            is_debug = False
            try:
                from django.conf import settings

                is_debug = getattr(settings, "DEBUG", False)
            except Exception:
                pass

            if is_debug:
                data = {
                    "error": {
                        "code": 500,
                        "message": f"Internal server error: {str(exc)}",
                        "type": "internal_error",
                    }
                }
            else:
                data = {
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "type": "internal_error",
                    }
                }

        return JsonResponse(data, status=status_code)


class APIError(Exception):
    """Base class for API-specific errors."""

    def __init__(self, message: str, code: int = 400, error_type: str = "api_error"):
        self.message = message
        self.code = code
        self.error_type = error_type
        super().__init__(message)


class ValidationAPIError(APIError):
    """Validation error for API requests."""

    def __init__(self, message: str, details: dict[str, Any] = None):
        super().__init__(message, 400, "validation_error")
        self.details = details or {}


class PermissionAPIError(APIError):
    """Permission error for API requests."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, 403, "permission_error")


class NotFoundAPIError(APIError):
    """Resource not found error for API requests."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404, "not_found_error")


class ConflictAPIError(APIError):
    """Conflict error for API requests."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, 409, "conflict_error")


class RateLimitAPIError(APIError):
    """Rate limit exceeded error for API requests."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429, "rate_limit_error")
