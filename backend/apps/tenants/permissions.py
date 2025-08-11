"""
Custom permissions for tenant models.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

from .models import Tenant, TenantUser, TenantInvitation

User = get_user_model()


class TenantPermission(permissions.BasePermission):
    """Permission class for Tenant operations."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Allow authenticated users to list tenants they belong to
        if view.action == 'list':
            return request.user.is_authenticated
        
        # Allow authenticated users to create tenants
        if view.action == 'create':
            return request.user.is_authenticated
        
        # For other actions, check object-level permissions
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Check if user is a member of the tenant
        if not hasattr(obj, 'tenant_users'):
            # This is a Tenant object
            is_member = obj.tenant_users.filter(
                user=request.user,
                is_active=True
            ).exists()
        else:
            # This is a TenantUser object
            is_member = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).exists()
        
        if not is_member:
            return False
        
        # Check specific permissions based on action
        if view.action in ['retrieve', 'summary', 'users', 'invitations']:
            # All members can view
            return True
        
        elif view.action in ['update', 'partial_update']:
            # Only owners and admins can update
            user_role = obj.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['destroy']:
            # Only owners can delete
            user_role = obj.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role == 'OWNER'
        
        elif view.action in ['suspend', 'activate']:
            # Only owners and admins can suspend/activate
            user_role = obj.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        return False


class TenantUserPermission(permissions.BasePermission):
    """Permission class for TenantUser operations."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Allow authenticated users to list tenant users
        if view.action == 'list':
            return request.user.is_authenticated
        
        # Allow authenticated users to create tenant users
        if view.action == 'create':
            return request.user.is_authenticated
        
        # Allow authenticated users to view their memberships
        if view.action == 'my_memberships':
            return request.user.is_authenticated
        
        # For other actions, check object-level permissions
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Check if user is a member of the tenant
        is_member = obj.tenant.tenant_users.filter(
            user=request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            return False
        
        # Check specific permissions based on action
        if view.action in ['retrieve']:
            # All members can view
            return True
        
        elif view.action in ['update', 'partial_update']:
            # Only owners and admins can update
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['destroy']:
            # Only owners and admins can delete
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['activate', 'deactivate']:
            # Only owners and admins can activate/deactivate
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        return False


class TenantInvitationPermission(permissions.BasePermission):
    """Permission class for TenantInvitation operations."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Allow authenticated users to list invitations
        if view.action == 'list':
            return request.user.is_authenticated
        
        # Allow authenticated users to create invitations
        if view.action == 'create':
            return request.user.is_authenticated
        
        # Allow authenticated users to view their invitations
        if view.action in ['my_invitations', 'pending']:
            return request.user.is_authenticated
        
        # For other actions, check object-level permissions
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Check if user is a member of the tenant
        is_member = obj.tenant.tenant_users.filter(
            user=request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            return False
        
        # Check specific permissions based on action
        if view.action in ['retrieve']:
            # All members can view
            return True
        
        elif view.action in ['update', 'partial_update']:
            # Only owners and admins can update
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['destroy']:
            # Only owners and admins can delete
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['resend']:
            # Only owners and admins can resend
            user_role = obj.tenant.tenant_users.filter(
                user=request.user,
                is_active=True
            ).first()
            return user_role and user_role.role in ['OWNER', 'ADMIN']
        
        elif view.action in ['respond']:
            # Users can respond to invitations sent to their email
            return obj.email == request.user.email
        
        return False


class IsTenantMember(permissions.BasePermission):
    """Permission class to check if user is a member of a specific tenant."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Get tenant from object
        tenant = None
        if hasattr(obj, 'tenant'):
            tenant = obj.tenant
        elif hasattr(obj, 'tenant_users'):
            tenant = obj
        
        if not tenant:
            return False
        
        # Check if user is a member of the tenant
        is_member = tenant.tenant_users.filter(
            user=request.user,
            is_active=True
        ).exists()
        
        return is_member


class IsTenantOwnerOrAdmin(permissions.BasePermission):
    """Permission class to check if user is owner or admin of a tenant."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Get tenant from object
        tenant = None
        if hasattr(obj, 'tenant'):
            tenant = obj.tenant
        elif hasattr(obj, 'tenant_users'):
            tenant = obj
        
        if not tenant:
            return False
        
        # Check if user is owner or admin of the tenant
        user_role = tenant.tenant_users.filter(
            user=request.user,
            is_active=True
        ).first()
        
        return user_role and user_role.role in ['OWNER', 'ADMIN']


class IsTenantOwner(permissions.BasePermission):
    """Permission class to check if user is owner of a tenant."""
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to perform the action on the object."""
        # Allow superusers to do anything
        if request.user.is_superuser:
            return True
        
        # Get tenant from object
        tenant = None
        if hasattr(obj, 'tenant'):
            tenant = obj.tenant
        elif hasattr(obj, 'tenant_users'):
            tenant = obj
        
        if not tenant:
            return False
        
        # Check if user is owner of the tenant
        user_role = tenant.tenant_users.filter(
            user=request.user,
            is_active=True
        ).first()
        
        return user_role and user_role.role == 'OWNER'
