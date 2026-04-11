"""
Authentication API endpoints.
"""

from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.http import HttpRequest
from ninja import Router
from ninja.responses import codes_2xx, codes_4xx, codes_5xx
from ninja.security import HttpBearer

from apps.accounts.schemas import CreateApiKeyIn

from ...accounts.models import ApiKey
from ...core.models import AuditLog, User
from ..schemas import ErrorResponse, SuccessResponse

router = Router(tags=["Authentication"])


class AuthBearer(HttpBearer):
    """JWT Bearer token authentication for protected endpoints."""

    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        """Authenticate JWT token."""
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

            # Check if token is expired
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                return None

            # Get user
            user_id = payload.get("user_id")
            if not user_id:
                return None

            try:
                user = User.objects.get(id=user_id, is_active=True)
                request.user = user
                return user
            except User.DoesNotExist:
                return None

        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None


@router.post(
    "/login",
    response={
        codes_2xx: SuccessResponse,
        codes_4xx: ErrorResponse,
        codes_5xx: ErrorResponse,
    },
)
def login_user(request, email: str, password: str):
    """User login endpoint with JWT token generation."""
    try:
        # Authenticate user
        user = authenticate(username=email, password=password)
        if not user or not user.is_active:
            return {
                "success": False,
                "message": "Invalid credentials",
                "error": "Invalid email or password",
            }, 401

        # Check if user is locked
        if user.is_locked():
            return {
                "success": False,
                "message": "Account locked",
                "error": "Account is temporarily locked due to failed login attempts",
            }, 423

        # Reset failed login attempts
        user.reset_failed_login()

        # Generate JWT tokens
        access_token = _generate_access_token(user)
        refresh_token = _generate_refresh_token(user)

        # Log successful login
        AuditLog.objects.create(
            user=user,
            action="LOGIN",
            resource_type="USER",
            resource_id=str(user.id),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds(),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "two_factor_enabled": user.two_factor_enabled,
                },
            },
        }

    except Exception as e:
        # Increment failed login attempts
        if user:
            user.increment_failed_login()

        return {"success": False, "message": "Login failed", "error": str(e)}, 500


@router.post("/refresh")
def refresh_token(request, refresh_token: str):
    """Refresh JWT access token."""
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token, settings.JWT_REFRESH_TOKEN_SECRET_KEY, algorithms=["HS256"]
        )

        # Check if token is expired
        if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            return {
                "success": False,
                "message": "Token expired",
                "error": "Refresh token has expired",
            }, 401

        # Get user
        user_id = payload.get("user_id")
        if not user_id:
            return {
                "success": False,
                "message": "Invalid token",
                "error": "Invalid refresh token",
            }, 401

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return {
                "success": False,
                "message": "User not found",
                "error": "User account not found or inactive",
            }, 404

        # Generate new access token
        new_access_token = _generate_access_token(user)

        return {
            "success": True,
            "message": "Token refreshed",
            "data": {
                "access_token": new_access_token,
                "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds(),
            },
        }

    except jwt.InvalidTokenError:
        return {
            "success": False,
            "message": "Invalid token",
            "error": "Invalid refresh token",
        }, 401
    except Exception as e:
        return {
            "success": False,
            "message": "Token refresh failed",
            "error": str(e),
        }, 500


@router.post("/logout")
def logout_user(request):
    """User logout endpoint."""
    try:
        # Get user from request (set by AuthBearer)
        user = getattr(request, "user", None)
        if not user:
            return {
                "success": False,
                "message": "Not authenticated",
                "error": "User not authenticated",
            }, 401

        # Log logout
        AuditLog.objects.create(
            user=user,
            action="LOGOUT",
            resource_type="USER",
            resource_id=str(user.id),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return {"success": True, "message": "Logout successful"}

    except Exception as e:
        return {"success": False, "message": "Logout failed", "error": str(e)}, 500


@router.get("/me")
def get_current_user(request):
    """Get current user profile."""
    try:
        user = getattr(request, "user", None)
        if not user:
            return {
                "success": False,
                "message": "Not authenticated",
                "error": "User not authenticated",
            }, 401

        return {
            "success": True,
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "date_of_birth": (
                        user.date_of_birth.isoformat() if user.date_of_birth else None
                    ),
                    "timezone": user.timezone,
                    "language": user.language,
                    "two_factor_enabled": user.two_factor_enabled,
                    "email_verified": user.email_verified,
                    "last_login": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                    "created_at": user.created_at.isoformat(),
                },
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get user profile",
            "error": str(e),
        }, 500


@router.post("/register")
def register_user(
    request,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str = "",
):
    """User registration endpoint."""
    try:
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return {
                "success": False,
                "message": "Registration failed",
                "error": "User with this email already exists",
            }, 409

        # Validate password strength
        if len(password) < 8:
            return {
                "success": False,
                "message": "Registration failed",
                "error": "Password must be at least 8 characters long",
            }, 400

        # Create user
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email_verified=False,  # Require email verification
            )

            # Log registration
            AuditLog.objects.create(
                user=user,
                action="CREATE",
                resource_type="USER",
                resource_id=str(user.id),
                ip_address=_get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "user_id": str(user.id),
                "email": user.email,
                "message": "Please check your email to verify your account",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Registration failed",
            "error": str(e),
        }, 500


@router.post("/api-keys")
def create_api_key(request, payload: CreateApiKeyIn):
    user = getattr(request, "user", None)
    if not user:
        return {
            "success": False,
            "message": "Not authenticated",
            "error": "User not authenticated",
        }, 401

    api_key = ApiKey.create_with_key(
        user=user,
        name=payload.name,
        scopes=payload.scopes,
        expires_at=payload.expires_at,
    )

    AuditLog.objects.create(
        user=user,
        action="CREATE",
        resource_type="API_KEY",
        resource_id=str(api_key.id),
        ip_address=_get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        metadata={"key_name": payload.name, "scopes": payload.scopes},
    )

    return {
        "success": True,
        "message": "API key created successfully",
        "data": {
            "api_key_id": str(api_key.id),
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "full_key": api_key.get_full_key(),
            "scopes": api_key.scopes,
            "expires_at": (
                api_key.expires_at.isoformat() if api_key.expires_at else None
            ),
            "created_at": api_key.created_at.isoformat(),
        },
    }


@router.get("/api-keys")
def list_api_keys(request):
    """List API keys for the authenticated user."""
    try:
        user = getattr(request, "user", None)
        if not user:
            return {
                "success": False,
                "message": "Not authenticated",
                "error": "User not authenticated",
            }, 401

        # Get user's API keys
        api_keys = ApiKey.objects.filter().order_by("-created_at")

        return {
            "success": True,
            "data": {
                "api_keys": [
                    {
                        "id": str(key.id),
                        "name": key.name,
                        "key_prefix": key.key_prefix,
                        "scopes": key.scopes,
                        "expires_at": (
                            key.expires_at.isoformat() if key.expires_at else None
                        ),
                        "created_at": key.created_at.isoformat(),
                        "last_used_at": (
                            key.last_used_at.isoformat() if key.last_used_at else None
                        ),
                    }
                    for key in api_keys
                ]
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to list API keys",
            "error": str(e),
        }, 500


@router.delete("/api-keys/{api_key_id}")
def delete_api_key(request, api_key_id: str):
    """Delete API key."""
    try:
        user = getattr(request, "user", None)
        if not user:
            return {
                "success": False,
                "message": "Not authenticated",
                "error": "User not authenticated",
            }, 401

        # Get and delete API key
        try:
            api_key = ApiKey.objects.get(id=api_key_id, user=user, is_active=True)
        except ApiKey.DoesNotExist:
            return {
                "success": False,
                "message": "API key not found",
                "error": "API key does not exist or access denied",
            }, 404

        # Soft delete
        api_key.is_active = False
        api_key.save()

        # Log deletion
        AuditLog.objects.create(
            user=user,
            action="DELETE",
            resource_type="API_KEY",
            resource_id=str(api_key.id),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"key_name": api_key.name},
        )

        return {"success": True, "message": "API key deleted successfully"}

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to delete API key",
            "error": str(e),
        }, 500


# Helper functions


def _generate_access_token(user: User) -> str:
    """Generate JWT access token."""
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + settings.JWT_ACCESS_TOKEN_LIFETIME,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def _generate_refresh_token(user: User) -> str:
    """Generate JWT refresh token."""
    payload = {
        "user_id": str(user.id),
        "exp": datetime.utcnow() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_REFRESH_TOKEN_SECRET_KEY, algorithm="HS256")


def _get_client_ip(request: HttpRequest) -> str:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip
