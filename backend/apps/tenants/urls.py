"""
URL configuration for tenant app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TenantViewSet, TenantUserViewSet, TenantInvitationViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'tenant-users', TenantUserViewSet, basename='tenant-user')
router.register(r'tenant-invitations', TenantInvitationViewSet, basename='tenant-invitation')

app_name = 'tenants'

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
    
    # Additional custom endpoints can be added here if needed
    # path('custom-endpoint/', CustomView.as_view(), name='custom-endpoint'),
]
