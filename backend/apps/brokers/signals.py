"""
Django signals for brokers app.
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import BrokerConnection, BrokerAccount, BrokerConnectionLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BrokerConnection)
def broker_connection_post_save_handler(sender, instance, created, **kwargs):
    """Handle broker connection creation and updates."""
    try:
        if created:
            # Log connection creation
            BrokerConnectionLog.objects.create(
                tenant=instance.tenant,
                broker_connection=instance,
                event_type='CONNECT',
                message=f"Broker connection '{instance.name}' created",
                level='INFO',
                metadata={
                    'broker_type': instance.broker.broker_type,
                    'host': instance.host_override or instance.broker.host,
                    'port': instance.port_override or instance.broker.port,
                    'use_ssl': instance.use_ssl_override if instance.use_ssl_override is not None else instance.broker.use_ssl,
                }
            )
            logger.info(f"Broker connection '{instance.name}' created for tenant {instance.tenant.name}")
        else:
            # Log connection updates
            BrokerConnectionLog.objects.create(
                tenant=instance.tenant,
                broker_connection=instance,
                event_type='API_CALL',
                message=f"Broker connection '{instance.name}' updated",
                level='INFO',
                metadata={
                    'status': instance.status,
                    'last_connected': instance.last_connected.isoformat() if instance.last_connected else None,
                    'last_disconnected': instance.last_disconnected.isoformat() if instance.last_disconnected else None,
                }
            )
            logger.info(f"Broker connection '{instance.name}' updated for tenant {instance.tenant.name}")
            
    except Exception as e:
        logger.error(f"Error handling broker connection post_save for {instance.name}: {e}")


@receiver(pre_save, sender=BrokerConnection)
def broker_connection_pre_save_handler(sender, instance, **kwargs):
    """Handle broker connection status changes."""
    try:
        if instance.pk:  # Only for updates, not new instances
            old_instance = BrokerConnection.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                # Log status change
                BrokerConnectionLog.objects.create(
                    tenant=instance.tenant,
                    broker_connection=instance,
                    event_type='CONNECT' if instance.status == 'CONNECTED' else 'DISCONNECT',
                    message=f"Broker connection '{instance.name}' status changed from {old_instance.status} to {instance.status}",
                    level='INFO',
                    metadata={
                        'old_status': old_instance.status,
                        'new_status': instance.status,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                # Update connection timestamps
                if instance.status == 'CONNECTED':
                    instance.last_connected = timezone.now()
                elif instance.status == 'DISCONNECTED':
                    instance.last_disconnected = timezone.now()
                    
                logger.info(f"Broker connection '{instance.name}' status changed: {old_instance.status} -> {instance.status}")
                
    except BrokerConnection.DoesNotExist:
        # New instance, nothing to compare
        pass
    except Exception as e:
        logger.error(f"Error handling broker connection pre_save for {instance.name}: {e}")


@receiver(post_delete, sender=BrokerConnection)
def broker_connection_post_delete_handler(sender, instance, **kwargs):
    """Handle broker connection deletion."""
    try:
        # Log connection deletion
        BrokerConnectionLog.objects.create(
            tenant=instance.tenant,
            broker_connection=instance,
            event_type='DISCONNECT',
            message=f"Broker connection '{instance.name}' deleted",
            level='INFO',
            metadata={
                'broker_type': instance.broker.broker_type,
                'deleted_at': timezone.now().isoformat(),
            }
        )
        
        logger.info(f"Broker connection '{instance.name}' deleted for tenant {instance.tenant.name}")
        
    except Exception as e:
        logger.error(f"Error handling broker connection post_delete for {instance.name}: {e}")


@receiver(post_save, sender=BrokerAccount)
def broker_account_post_save_handler(sender, instance, created, **kwargs):
    """Handle broker account creation and updates."""
    try:
        if created:
            logger.info(f"Broker account '{instance.account_name}' created for tenant {instance.tenant.name}")
        else:
            logger.info(f"Broker account '{instance.account_name}' updated for tenant {instance.tenant.name}")
            
    except Exception as e:
        logger.error(f"Error handling broker account post_save for {instance.account_name}: {e}")


@receiver(post_delete, sender=BrokerAccount)
def broker_account_post_delete_handler(sender, instance, **kwargs):
    """Handle broker account deletion."""
    try:
        logger.info(f"Broker account '{instance.account_name}' deleted for tenant {instance.tenant.name}")
        
    except Exception as e:
        logger.error(f"Error handling broker account post_delete for {instance.account_name}: {e}")


# Signal to handle connection health monitoring
@receiver(post_save, sender=BrokerConnectionLog)
def broker_connection_log_post_save_handler(sender, instance, created, **kwargs):
    """Handle broker connection log creation for monitoring."""
    try:
        if created and instance.level in ['ERROR', 'CRITICAL']:
            # Log critical errors for monitoring
            logger.error(
                f"Broker connection error for {instance.broker_connection.name}: "
                f"{instance.message} (Level: {instance.level})"
            )
            
            # Could emit webhook notifications here for critical errors
            # or trigger alerting systems
            
    except Exception as e:
        logger.error(f"Error handling broker connection log post_save: {e}")
