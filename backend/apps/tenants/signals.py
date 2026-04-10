"""
Signals for tenant models.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Tenant, TenantInvitation, TenantUser

User = get_user_model()


def clear_cache(pattern):
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        cache.clear()


@receiver(post_save, sender=Tenant)
def tenant_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Tenant model."""
    clear_cache(f"tenant_{instance.id}_*")


@receiver(post_delete, sender=Tenant)
def tenant_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for Tenant model."""
    clear_cache(f"tenant_{instance.id}_*")


@receiver(post_save, sender=TenantUser)
def tenant_user_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for TenantUser model."""
    clear_cache(f"tenant_{instance.tenant.id}_users_*")


@receiver(post_delete, sender=TenantUser)
def tenant_user_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for TenantUser model."""
    clear_cache(f"tenant_{instance.tenant.id}_users_*")


@receiver(post_save, sender=TenantInvitation)
def tenant_invitation_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for TenantInvitation model."""
    clear_cache(f"tenant_{instance.tenant.id}_invitations_*")


@receiver(pre_save, sender=TenantInvitation)
def tenant_invitation_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for TenantInvitation model."""
    pass


@receiver(post_delete, sender=TenantInvitation)
def tenant_invitation_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for TenantInvitation model."""
    clear_cache(f"tenant_{instance.tenant.id}_invitations_*")
