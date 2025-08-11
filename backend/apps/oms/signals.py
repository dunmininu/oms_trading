"""
Django signals for OMS app.
"""

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from django.db import transaction

from .models import Order, Execution, Position, PnLSnapshot
from apps.core.models import AuditLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def order_post_save_handler(sender, instance, created, **kwargs):
    """Handle order creation and updates."""
    try:
        if created:
            # Log order creation
            AuditLog.objects.create(
                tenant=instance.tenant,
                user=instance.user,
                action='ORDER_CREATED',
                resource_type='Order',
                resource_id=str(instance.id),
                metadata={
                    'order_type': instance.order_type,
                    'side': instance.side,
                    'quantity': str(instance.quantity),
                    'price': str(instance.price) if instance.price else None,
                    'instrument_symbol': instance.instrument.symbol,
                    'broker_account': instance.broker_account.account_name,
                }
            )
            logger.info(f"Order created: {instance.client_order_id} - {instance.side} {instance.quantity} {instance.instrument.symbol}")
        else:
            # Log order updates
            AuditLog.objects.create(
                tenant=instance.tenant,
                user=instance.user,
                action='ORDER_UPDATED',
                resource_type='Order',
                resource_id=str(instance.id),
                metadata={
                    'old_state': getattr(instance, '_old_state', 'UNKNOWN'),
                    'new_state': instance.state,
                    'filled_quantity': str(instance.filled_quantity),
                    'average_price': str(instance.average_price) if instance.average_price else None,
                }
            )
            logger.info(f"Order updated: {instance.client_order_id} - State: {instance.state}")
            
    except Exception as e:
        logger.error(f"Error handling order post_save for {instance.client_order_id}: {e}")


@receiver(pre_save, sender=Order)
def order_pre_save_handler(sender, instance, **kwargs):
    """Handle order state changes and track old state."""
    try:
        if instance.pk:  # Only for updates, not new instances
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_state = old_instance.state
            
            # Check if order was filled
            if (old_instance.state not in ['FILLED', 'PARTIALLY_FILLED'] and 
                instance.state in ['FILLED', 'PARTIALLY_FILLED']):
                instance.filled_at = timezone.now()
                
            # Check if order was cancelled
            if (old_instance.state not in ['CANCELLED', 'REJECTED', 'EXPIRED'] and 
                instance.state in ['CANCELLED', 'REJECTED', 'EXPIRED']):
                instance.cancelled_at = timezone.now()
                
    except Order.DoesNotExist:
        # New instance, nothing to compare
        pass
    except Exception as e:
        logger.error(f"Error handling order pre_save for {instance.client_order_id}: {e}")


@receiver(post_save, sender=Execution)
def execution_post_save_handler(sender, instance, created, **kwargs):
    """Handle execution creation and update positions."""
    try:
        if created:
            # Log execution
            AuditLog.objects.create(
                tenant=instance.tenant,
                user=instance.order.user,
                action='EXECUTION_CREATED',
                resource_type='Execution',
                resource_id=str(instance.id),
                metadata={
                    'execution_id': instance.execution_id,
                    'order_id': str(instance.order.id),
                    'quantity': str(instance.quantity),
                    'price': str(instance.price),
                    'commission': str(instance.commission),
                    'instrument_symbol': instance.order.instrument.symbol,
                }
            )
            
            # Update position
            update_position_from_execution(instance)
            
            logger.info(f"Execution created: {instance.execution_id} - {instance.quantity} @ {instance.price}")
            
    except Exception as e:
        logger.error(f"Error handling execution post_save for {instance.execution_id}: {e}")


@receiver(post_save, sender=Position)
def position_post_save_handler(sender, instance, created, **kwargs):
    """Handle position creation and updates."""
    try:
        if created:
            logger.info(f"Position created: {instance.instrument.symbol} - {instance.quantity}")
        else:
            logger.info(f"Position updated: {instance.instrument.symbol} - {instance.quantity} @ {instance.average_cost}")
            
    except Exception as e:
        logger.error(f"Error handling position post_save for {instance.instrument.symbol}: {e}")


def update_position_from_execution(execution):
    """Update position based on execution."""
    try:
        with transaction.atomic():
            order = execution.order
            instrument = order.instrument
            broker_account = order.broker_account
            tenant = order.tenant
            
            # Get or create position
            position, created = Position.objects.get_or_create(
                tenant=tenant,
                broker_account=broker_account,
                instrument=instrument,
                defaults={
                    'quantity': Decimal('0.0000'),
                    'average_cost': Decimal('0.0000'),
                }
            )
            
            # Calculate new position
            if order.side in ['BUY', 'BUY_TO_COVER']:
                # Long position
                new_quantity = position.quantity + execution.quantity
                if new_quantity != 0:
                    # Calculate new average cost
                    total_cost = (position.quantity * (position.average_cost or Decimal('0.0000')) + 
                                execution.quantity * execution.price)
                    new_average_cost = total_cost / new_quantity
                else:
                    new_average_cost = Decimal('0.0000')
            else:
                # Short position
                new_quantity = position.quantity - execution.quantity
                if new_quantity != 0:
                    # For short positions, average cost calculation is more complex
                    # For now, keep the existing average cost
                    new_average_cost = position.average_cost
                else:
                    new_average_cost = Decimal('0.0000')
            
            # Update position
            position.quantity = new_quantity
            position.average_cost = new_average_cost
            position.save()
            
            # Update order filled quantity and average price
            order.filled_quantity += execution.quantity
            if order.average_price:
                # Calculate new average price
                total_value = (order.average_price * (order.filled_quantity - execution.quantity) + 
                             execution.price * execution.quantity)
                order.average_price = total_value / order.filled_quantity
            else:
                order.average_price = execution.price
            
            # Update order state
            if order.filled_quantity >= order.quantity:
                order.state = 'FILLED'
                order.filled_at = timezone.now()
            elif order.filled_quantity > 0:
                order.state = 'PARTIALLY_FILLED'
            
            order.save()
            
            logger.info(f"Position updated for {instrument.symbol}: {new_quantity} @ {new_average_cost}")
            
    except Exception as e:
        logger.error(f"Error updating position from execution {execution.execution_id}: {e}")


# Signal to handle daily P&L snapshots
@receiver(post_save, sender=Position)
def position_pnl_snapshot_handler(sender, instance, **kwargs):
    """Handle position updates for P&L snapshots."""
    try:
        # This could trigger a task to update daily P&L snapshots
        # For now, just log the position update
        pass
        
    except Exception as e:
        logger.error(f"Error handling position P&L snapshot for {instance.instrument.symbol}: {e}")


# Signal to handle order state machine transitions
@receiver(post_save, sender=Order)
def order_state_machine_handler(sender, instance, **kwargs):
    """Handle order state machine transitions."""
    try:
        # This could trigger additional business logic based on state changes
        # For example, sending notifications, updating risk metrics, etc.
        
        if instance.state == 'FILLED':
            # Order completely filled - could trigger strategy completion
            pass
        elif instance.state == 'REJECTED':
            # Order rejected - could trigger risk review
            pass
        elif instance.state == 'CANCELLED':
            # Order cancelled - could trigger cleanup tasks
            pass
            
    except Exception as e:
        logger.error(f"Error handling order state machine for {instance.client_order_id}: {e}")
