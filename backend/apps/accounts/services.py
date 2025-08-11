"""
Authentication services for the accounts app.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, Dict, Any
import secrets
import hashlib

from apps.core.models import User
from .models import ApiKey
from .repositories import UserRepository, ApiKeyRepository


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        # Prefer repository pattern for consistency with services
        user = authenticate(username=username, password=password)
        if user and user.is_active and not user.is_locked():
            # Reset failed login attempts on successful login
            user.reset_failed_login()
            return user
        elif user and user.is_locked():
            # Increment failed login attempts
            user.increment_failed_login()
        return None
    
    @staticmethod
    def create_user(username: str, email: str, password: str, 
                   first_name: str = "", last_name: str = "") -> User:
        """Create a new user with validation."""
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(f"Password validation failed: {e}")
        
        # Check if user already exists
        if UserRepository(User).exists_with_email(email):
            raise ValidationError("Email already exists")
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return user
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> bool:
        """Change user password with validation."""
        # Verify current password
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect")
        
        # Validate new password
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise ValidationError(f"New password validation failed: {e}")
        
        # Change password
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.save()
        
        return True
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_api_key(user: User, tenant_id: str, name: str, scopes: list = None) -> ApiKey:
        """Create a new API key for user."""
        # Create API key using the new model
        api_key = ApiKey.create_with_key(
            user=user,
            tenant_id=tenant_id,
            name=name,
            scopes=scopes or []
        )
        
        return api_key
    
    @staticmethod
    def validate_api_key(key: str) -> Optional[ApiKey]:
        """Validate API key and return associated user."""
        # Hash the provided key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        repo = ApiKeyRepository(ApiKey)
        api_key = repo.get_active_by_hash(key_hash)
        if not api_key or api_key.is_expired():
            return None
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=['last_used_at'])
        return api_key
    
    @staticmethod
    def revoke_api_key(api_key: ApiKey) -> bool:
        """Revoke an API key."""
        api_key.is_active = False
        api_key.save(update_fields=['is_active', 'updated_at'])
        return True
    
    @staticmethod
    def generate_password_reset_token(user: User) -> str:
        """Generate password reset token."""
        token = secrets.token_urlsafe(32)
        user.verification_token = token
        user.verification_expires = timezone.now() + timezone.timedelta(hours=24)
        user.save()
        return token
    
    @staticmethod
    def validate_password_reset_token(user: User, token: str) -> bool:
        """Validate password reset token."""
        if (user.verification_token == token and 
            user.verification_expires and 
            user.verification_expires > timezone.now()):
            return True
        return False
    
    @staticmethod
    def reset_password_with_token(user: User, token: str, new_password: str) -> bool:
        """Reset password using token."""
        if not AuthService.validate_password_reset_token(user, token):
            raise ValidationError("Invalid or expired token")
        
        # Validate new password
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise ValidationError(f"Password validation failed: {e}")
        
        # Reset password
        user.set_password(new_password)
        user.verification_token = None
        user.verification_expires = None
        user.last_password_change = timezone.now()
        user.save()
        
        return True


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def update_user_profile(user: User, **kwargs) -> User:
        """Update user profile information."""
        allowed_fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'bio', 'timezone', 'language',
            'email_notifications', 'sms_notifications'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.save()
        return user
    
    @staticmethod
    def deactivate_user(user: User) -> bool:
        """Deactivate user account."""
        user.is_active = False
        user.save()
        return True
    
    @staticmethod
    def activate_user(user: User) -> bool:
        """Activate user account."""
        user.is_active = True
        user.save()
        return True
    
    @staticmethod
    def lock_user(user: User, duration_minutes: int = 30) -> bool:
        """Lock user account for specified duration."""
        user.locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        user.save()
        return True
    
    @staticmethod
    def unlock_user(user: User) -> bool:
        """Unlock user account."""
        user.locked_until = None
        user.failed_login_attempts = 0
        user.save()
        return True
