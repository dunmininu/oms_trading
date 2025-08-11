"""
Signals for tenant models.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Tenant, TenantUser, TenantInvitation

User = get_user_model()


@receiver(post_save, sender=Tenant)
def tenant_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for Tenant model."""
    if created:
        # Clear cache for tenant-related queries
        cache.delete_pattern(f'tenant_{instance.id}_*')
        
        # Log tenant creation
        from django.contrib.admin.models import LogEntry, CHANGE
        LogEntry.objects.log_action(
            user_id=1,  # System user
            content_type_id=1,  # Will be set properly in actual implementation
            object_id=instance.id,
            object_repr=str(instance),
            action_flag=CHANGE,
            change_message="Tenant created"
        )
    
    # Clear cache for tenant-related queries
    cache.delete_pattern(f'tenant_{instance.id}_*')


@receiver(post_delete, sender=Tenant)
def tenant_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for Tenant model."""
    # Clear cache for tenant-related queries
    cache.delete_pattern(f'tenant_{instance.id}_*')
    
    # Log tenant deletion
    from django.contrib.admin.models import LogEntry, CHANGE
    LogEntry.objects.log_action(
        user_id=1,  # System user
        content_type_id=1,  # Will be set properly in actual implementation
        object_id=instance.id,
        object_repr=str(instance),
        action_flag=CHANGE,
        change_message="Tenant deleted"
    )


@receiver(post_save, sender=TenantUser)
def tenant_user_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for TenantUser model."""
    if created:
        # Clear cache for tenant user queries
        cache.delete_pattern(f'tenant_{instance.tenant.id}_users_*')
        
        # Log user addition to tenant
        from django.contrib.admin.models import LogEntry, CHANGE
        LogEntry.objects.log_action(
            user_id=1,  # System user
            content_type_id=1,  # Will be set properly in actual implementation
            object_id=instance.id,
            object_repr=str(instance),
            action_flag=CHANGE,
            change_message=f"User {instance.user.email} added to tenant {instance.tenant.name}"
        )
    
    # Clear cache for tenant user queries
    cache.delete_pattern(f'tenant_{instance.tenant.id}_users_*')


@receiver(post_delete, sender=TenantUser)
def tenant_user_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for TenantUser model."""
    # Clear cache for tenant user queries
    cache.delete_pattern(f'tenant_{instance.tenant.id}_users_*')
    
    # Log user removal from tenant
    from django.contrib.admin.models import LogEntry, CHANGE
    LogEntry.objects.log_action(
        user_id=1,  # System user
        content_type_id=1,  # Will be set properly in actual implementation
        object_id=instance.id,
        object_repr=str(instance),
        action_flag=CHANGE,
        change_message=f"User {instance.user.email} removed from tenant {instance.tenant.name}"
    )


@receiver(post_save, sender=TenantInvitation)
def tenant_invitation_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for TenantInvitation model."""
    if created:
        # Clear cache for tenant invitation queries
        cache.delete_pattern(f'tenant_{instance.tenant.id}_invitations_*')
        
        # Log invitation creation
        from django.contrib.admin.models import LogEntry, CHANGE
        LogEntry.objects.log_action(
            user_id=1,  # System user
            content_type_id=1,  # Will be set properly in actual implementation
            object_id=instance.id,
            object_repr=str(instance),
            action_flag=CHANGE,
            change_message=f"Invitation sent to {instance.email} for tenant {instance.tenant.name}"
        )
    
    # Clear cache for tenant invitation queries
    cache.delete_pattern(f'tenant_{instance.tenant.id}_invitations_*')


@receiver(pre_save, sender=TenantInvitation)
def tenant_invitation_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for TenantInvitation model."""
    if instance.pk:  # Only for updates
        try:
            old_instance = TenantInvitation.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed, log the change
                from django.contrib.admin.models import LogEntry, CHANGE
                LogEntry.objects.log_action(
                    user_id=1,  # System user
                    content_type_id=1,  # Will be set properly in actual implementation
                    object_id=instance.id,
                    object_repr=str(instance),
                    action_flag=CHANGE,
                    change_message=f"Invitation status changed from {old_instance.status} to {instance.status}"
                )
        except TenantInvitation.DoesNotExist:
            pass


@receiver(post_delete, sender=TenantInvitation)
def tenant_invitation_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for TenantInvitation model."""
    # Clear cache for tenant invitation queries
    cache.delete_pattern(f'tenant_{instance.tenant.id}_invitations_*')
    
    # Log invitation deletion
    from django.contrib.admin.models import LogEntry, CHANGE
    LogEntry.objects.log_action(
        user_id=1,  # System user
        content_type_id=1,  # Will be set properly in actual implementation
        object_id=instance.id,
        object_repr=str(instance),
        action_flag=CHANGE,
        change_message=f"Invitation to {instance.email} for tenant {instance.tenant.name} deleted"
    )
