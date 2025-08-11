"""
API middleware for Django Ninja.
"""

from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings
from typing import Optional
import time


class TenantMiddleware:
    """Middleware for tenant resolution and request scoping."""
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        """Process request and add tenant context."""
        # Extract tenant from subdomain, header, or query param
        tenant_id = self._extract_tenant_id(request)
        
        if tenant_id:
            request.tenant_id = tenant_id
            # Cache tenant info for performance
            cache_key = f"tenant_{tenant_id}_info"
            tenant_info = cache.get(cache_key)
            if not tenant_info:
                # TODO: Fetch tenant info from database
                tenant_info = {"id": tenant_id, "name": "Default Tenant"}
                cache.set(cache_key, tenant_info, 300)  # 5 minutes
            request.tenant_info = tenant_info
        
        return self.get_response(request) if self.get_response else None
    
    def _extract_tenant_id(self, request: HttpRequest) -> Optional[str]:
        """Extract tenant ID from request."""
        # Check subdomain first
        host = request.get_host()
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain not in ['www', 'api', 'localhost', '127']:
                # TODO: Lookup tenant by subdomain
                return subdomain
        
        # Check header
        tenant_header = request.headers.get('X-Tenant-ID')
        if tenant_header:
            return tenant_header
        
        # Check query param
        tenant_param = request.GET.get('tenant_id')
        if tenant_param:
            return tenant_param
        
        return None


class RateLimitMiddleware:
    """Middleware for API rate limiting."""
    
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        """Process request and apply rate limiting."""
        # Skip rate limiting for health checks
        if request.path in ['/health', '/']:
            return self.get_response(request) if self.get_response else None
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id, request.path):
            from ninja.errors import HttpError
            raise HttpError(429, "Rate limit exceeded")
        
        return self.get_response(request) if self.get_response else None
    
    def _get_client_id(self, request: HttpRequest) -> str:
        """Get unique client identifier for rate limiting."""
        # Use API key if available
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: Extract user/tenant from JWT token
            return f"user_{token[:8]}"
        
        # Fallback to IP address
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip_{ip}"
    
    def _check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check if request is within rate limits."""
        # Get rate limit configuration
        rate_limit = getattr(settings, 'API_RATE_LIMIT', 100)  # requests per minute
        rate_limit_window = getattr(settings, 'API_RATE_LIMIT_WINDOW', 60)  # seconds
        
        # Create cache key
        cache_key = f"rate_limit_{client_id}_{endpoint}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= rate_limit:
            return False
        
        # Increment count
        cache.set(cache_key, current_count + 1, rate_limit_window)
        return True
