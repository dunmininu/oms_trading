"""
User models for the accounts app.
"""

from apps.core.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone


class ApiKey(BaseModel):
    """API key for machine-to-machine authentication."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='api_keys')
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key_prefix = models.CharField(max_length=8, unique=True)
    key_hash = models.CharField(max_length=128)  # SHA256 hash of the full key
    scopes = models.JSONField(default=list)  # List of permission scopes
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_api_key'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
    def is_expired(self):
        """Check if API key is expired."""
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False
    
    def has_scope(self, scope: str) -> bool:
        """Check if API key has the specified scope."""
        if not self.is_active or self.is_expired():
            return False
        
        # Check if scope is in the scopes list
        return scope in self.scopes
    
    def has_any_scope(self, scopes: list) -> bool:
        """Check if API key has any of the specified scopes."""
        if not self.is_active or self.is_expired():
            return False
        
        return any(scope in self.scopes for scope in scopes)
    
    def get_full_key(self):
        """Get the full API key (only available during creation)."""
        # This should only be called during creation
        if hasattr(self, '_full_key'):
            return self._full_key
        return None
    
    def save(self, *args, **kwargs):
        """Override save to generate key if not provided."""
        if not self.key_prefix:
            # Generate a unique key prefix
            import secrets
            self.key_prefix = f"oms_{secrets.token_hex(4)}"
        
        super().save(*args, **kwargs)
    
    @classmethod
    def create_with_key(cls, **kwargs):
        """Create API key with generated full key."""
        import secrets
        import hashlib
        
        # Generate the full key
        full_key = f"oms_{secrets.token_hex(32)}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Create the instance
        instance = cls(**kwargs)
        instance.key_hash = key_hash
        
        # Store the full key temporarily for return
        instance._full_key = full_key
        
        # Save and return
        instance.save()
        return instance


class UserSession(BaseModel):
    """User session tracking for security."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_user_session'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
    
    def __str__(self):
        return f"Session {self.session_key} for {self.user.email}"
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
