"""
Core middleware for OMS Trading system.
"""

import uuid
import logging
from django.http import HttpRequest
from django.utils import timezone
from django.conf import settings
from typing import Optional

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """Middleware for adding unique request ID to all requests."""
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        """Add request ID to request."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Add to response headers
        response = self.get_response(request) if self.get_response else None
        if response:
            response['X-Request-ID'] = request_id
        
        return response


class AuditLogMiddleware:
    """Middleware for automatic audit logging."""
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        """Process request and log audit trail."""
        # Skip audit logging for certain paths
        if self._should_skip_audit(request.path):
            return self.get_response(request) if self.get_response else None
        
        # Process request
        response = self.get_response(request) if self.get_response else None
        
        # Log audit trail
        self._log_audit_trail(request, response)
        
        return response
    
    def _should_skip_audit(self, path: str) -> bool:
        """Check if audit logging should be skipped for this path."""
        skip_paths = [
            '/health',
            '/static/',
            '/media/',
            '/admin/jsi18n/',
            '/favicon.ico',
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _log_audit_trail(self, request: HttpRequest, response):
        """Log audit trail for the request."""
        try:
            # Only log if audit logging is enabled
            if not getattr(settings, 'AUDIT_LOG_ENABLED', True):
                return
            
            # Get user from request
            user = getattr(request, 'user', None)
            user_id = str(user.id) if user and user.is_authenticated else None
            
            # Get tenant from request
            tenant_id = getattr(request, 'tenant_id', None)
            
            # Determine action type
            action = self._determine_action(request.method, request.path)
            
            # Log to database if models are available
            if hasattr(request, 'user') and request.user.is_authenticated:
                self._log_to_database(
                    request=request,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    action=action,
                    response=response
                )
            
            # Log to structured logger
            self._log_to_logger(
                request=request,
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                response=response
            )
            
        except Exception as e:
            # Don't let audit logging errors break the request
            logger.error(f"Audit logging failed: {e}", exc_info=True)
    
    def _determine_action(self, method: str, path: str) -> str:
        """Determine the action type based on HTTP method and path."""
        if method == 'GET':
            return 'READ'
        elif method == 'POST':
            if 'login' in path:
                return 'LOGIN'
            elif 'logout' in path:
                return 'LOGOUT'
            else:
                return 'CREATE'
        elif method == 'PUT' or method == 'PATCH':
            return 'UPDATE'
        elif method == 'DELETE':
            return 'DELETE'
        else:
            return 'API_CALL'
    
    def _log_to_database(self, request: HttpRequest, user_id: Optional[str], 
                         tenant_id: Optional[str], action: str, response):
        """Log audit trail to database."""
        try:
            from .models import AuditLog
            
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Get request ID
            request_id = getattr(request, 'request_id', '')
            
            # Create audit log entry
            AuditLog.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type='API_ENDPOINT',
                resource_id=request.path,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                metadata={
                    'method': request.method,
                    'status_code': response.status_code if response else None,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'headers': dict(request.headers),
                }
            )
            
        except Exception as e:
            logger.error(f"Database audit logging failed: {e}", exc_info=True)
    
    def _log_to_logger(self, request: HttpRequest, user_id: Optional[str], 
                       tenant_id: Optional[str], action: str, response):
        """Log audit trail to structured logger."""
        log_data = {
            'request_id': getattr(request, 'request_id', ''),
            'user_id': user_id,
            'tenant_id': tenant_id,
            'action': action,
            'method': request.method,
            'path': request.path,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'status_code': response.status_code if response else None,
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info("Audit trail", extra=log_data)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
