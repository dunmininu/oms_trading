"""
API exception handling for Django Ninja.
"""

from ninja.errors import HttpError
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpRequest
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class APIExceptionHandler:
    """Centralized exception handling for API endpoints."""
    
    @staticmethod
    def handle_exception(request: HttpRequest, exc: Exception) -> Dict[str, Any]:
        """Handle exceptions and return consistent error responses."""
        
        # Log the exception
        logger.error(
            f"API Exception: {type(exc).__name__}: {str(exc)}",
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.META.get('REMOTE_ADDR', ''),
            },
            exc_info=True
        )
        
        # Handle specific exception types
        if isinstance(exc, HttpError):
            return {
                "error": {
                    "code": exc.status_code,
                    "message": str(exc),
                    "type": "http_error"
                }
            }
        
        elif isinstance(exc, ValidationError):
            return {
                "error": {
                    "code": 400,
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
                }
            }
        
        elif isinstance(exc, PermissionDenied):
            return {
                "error": {
                    "code": 403,
                    "message": "Permission denied",
                    "type": "permission_error"
                }
            }
        
        elif isinstance(exc, ValueError):
            return {
                "error": {
                    "code": 400,
                    "message": str(exc),
                    "type": "value_error"
                }
            }
        
        # Handle unexpected exceptions
        else:
            # In production, don't expose internal error details
            if getattr(request, 'settings', {}).get('DEBUG', False):
                return {
                    "error": {
                        "code": 500,
                        "message": f"Internal server error: {str(exc)}",
                        "type": "internal_error"
                    }
                }
            else:
                return {
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "type": "internal_error"
                    }
                }


class APIError(Exception):
    """Base class for API-specific errors."""
    
    def __init__(self, message: str, code: int = 400, error_type: str = "api_error"):
        self.message = message
        self.code = code
        self.error_type = error_type
        super().__init__(message)


class ValidationAPIError(APIError):
    """Validation error for API requests."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
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
