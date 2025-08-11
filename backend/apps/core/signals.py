"""
Django signals for core app.
"""

import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import User, AuditLog

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login events."""
    try:
        # Update last activity and IP address
        user.last_activity = timezone.now()
        if request:
            user.last_ip_address = request.META.get('REMOTE_ADDR')
        user.save(update_fields=['last_activity', 'last_ip_address'])
        
        # Log the login event
        if hasattr(request, 'tenant'):
            AuditLog.objects.create(
                tenant=request.tenant,
                user=user,
                action='LOGIN',
                resource_type='User',
                resource_id=str(user.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key or '',
                request_id=getattr(request, 'request_id', ''),
                metadata={
                    'login_method': 'password',
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
        
        logger.info(f"User {user.email} logged in successfully")
        
    except Exception as e:
        logger.error(f"Error handling user login for {user.email}: {e}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Handle user logout events."""
    try:
        if user and hasattr(request, 'tenant'):
            AuditLog.objects.create(
                tenant=request.tenant,
                user=user,
                action='LOGOUT',
                resource_type='User',
                resource_id=str(user.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key or '',
                request_id=getattr(request, 'request_id', ''),
                metadata={
                    'logout_method': 'manual',
                    'session_duration': None,  # Could calculate this if needed
                }
            )
        
        logger.info(f"User {user.email if user else 'Unknown'} logged out")
        
    except Exception as e:
        logger.error(f"Error handling user logout: {e}")


@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, **kwargs):
    """Handle user creation and updates."""
    try:
        if created:
            logger.info(f"New user created: {instance.email}")
        else:
            logger.info(f"User updated: {instance.email}")
            
    except Exception as e:
        logger.error(f"Error handling user post_save for {instance.email}: {e}")


@receiver(post_delete, sender=User)
def user_post_delete_handler(sender, instance, **kwargs):
    """Handle user deletion."""
    try:
        logger.info(f"User deleted: {instance.email}")
        
    except Exception as e:
        logger.error(f"Error handling user post_delete for {instance.email}: {e}")


# Middleware to track user activity
class UserActivityMiddleware:
    """Middleware to track user activity."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request and track user activity."""
        response = self.get_response(request)
        
        # Track user activity for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Update last activity (but not on every request to avoid DB writes)
                # This could be optimized with caching or periodic updates
                pass
            except Exception as e:
                logger.error(f"Error tracking user activity: {e}")
        
        return response
