"""
Repository implementations for accounts app using DjangoRepository.
"""

from typing import Optional, Dict, Any

from apps.api.base import DjangoRepository
from apps.core.models import User
from .models import ApiKey


class UserRepository(DjangoRepository[User]):
    """Repository for user data access operations."""

    def get_by_email(self, email: str) -> Optional[User]:
        try:
            return self.model.objects.get(email=email)
        except self.model.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            return self.model.objects.get(username=username)
        except self.model.DoesNotExist:
            return None

    def exists_with_email(self, email: str) -> bool:
        return self.model.objects.filter(email=email).exists()

    def exists_with_username(self, username: str) -> bool:
        return self.model.objects.filter(username=username).exists()


class ApiKeyRepository(DjangoRepository[ApiKey]):
    """Repository for API key operations."""

    def get_active_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        try:
            return self.model.objects.get(key_hash=key_hash, is_active=True)
        except self.model.DoesNotExist:
            return None

    def list_for_user(self, tenant_id: str, user: User):
        return self.model.objects.filter(
            tenant_id=tenant_id,
            user=user,
            is_active=True,
        ).order_by("-created_at")

    def soft_delete(self, api_key_id: str, tenant_id: str, user: User) -> bool:
        try:
            api_key = self.model.objects.get(
                id=api_key_id,
                tenant_id=tenant_id,
                user=user,
                is_active=True,
            )
        except self.model.DoesNotExist:
            return False

        api_key.is_active = False
        api_key.save(update_fields=["is_active", "updated_at"])
        return True

    def create_with_key(self, data: Dict[str, Any]) -> ApiKey:
        """Create API key using model's secure helper and return model instance.

        Expects: data with keys: tenant_id, user, name, scopes, expires_at (optional).
        """
        return self.model.create_with_key(
            tenant_id=data.get("tenant_id"),
            user=data.get("user"),
            name=data.get("name", ""),
            scopes=data.get("scopes") or [],
            expires_at=data.get("expires_at"),
        )


