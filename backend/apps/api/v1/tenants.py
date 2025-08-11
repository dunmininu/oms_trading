"""
Tenants API endpoints.
"""

from ninja import Router
from ninja import Query
from django.http import HttpRequest
from typing import Optional, List, Dict, Any
from django.core.paginator import Paginator

from ..schemas import (
    SuccessResponse, ErrorResponse, PaginatedResponse, 
    BaseFilterSchema, IDSchema, TimestampSchema, TenantSchema
)
from ..base import DjangoRepository, BaseService
from ...tenants.models import Tenant, TenantUser, TenantInvitation
from ...tenants.schemas import (
    TenantCreateSchema, TenantUpdateSchema, TenantResponseSchema,
    TenantUserCreateSchema, TenantUserUpdateSchema, TenantUserResponseSchema,
    TenantInvitationCreateSchema, TenantInvitationResponseSchema
)
from ..exceptions import NotFoundAPIError, PermissionAPIError

router = Router(tags=["Tenant Management"])


class TenantRepository(DjangoRepository[Tenant]):
    """Repository for tenant operations."""
    
    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> Tenant:
        """Get tenant by ID (no tenant filtering for tenant operations)."""
        try:
            return self.model.objects.get(id=id)
        except Tenant.DoesNotExist:
            raise NotFoundAPIError(f"Tenant with id {id} not found")
    
    def list(
        self, 
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List tenants with pagination and filtering."""
        queryset = self.model.objects.all()
        
        # Apply additional filters
        if filters:
            queryset = queryset.filter(**filters)
        
        # Apply ordering
        if ordering:
            queryset = queryset.order_by(ordering)
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'data': list(page_obj.object_list),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }


class TenantService(BaseService):
    """Service for tenant business logic."""
    
    def __init__(self):
        super().__init__(TenantRepository(Tenant))
    
    def create_tenant(self, data: Dict[str, Any], user_id: str) -> Tenant:
        """Create a new tenant."""
        # Validate permissions
        if not self.validate_permissions(user_id, "create", "tenant"):
            raise PermissionAPIError("Insufficient permissions to create tenant")
        
        # Create tenant
        tenant = self.repository.create(data)
        
        # Log audit trail
        self.audit_log(
            action="create",
            resource_type="tenant",
            resource_id=str(tenant.id),
            user_id=user_id
        )
        
        return tenant
    
    def update_tenant(self, tenant_id: str, data: Dict[str, Any], user_id: str) -> Tenant:
        """Update existing tenant."""
        # Validate permissions
        if not self.validate_permissions(user_id, "update", "tenant"):
            raise PermissionAPIError("Insufficient permissions to update tenant")
        
        # Update tenant
        tenant = self.repository.update(tenant_id, data)
        
        # Log audit trail
        self.audit_log(
            action="update",
            resource_type="tenant",
            resource_id=tenant_id,
            user_id=user_id
        )
        
        return tenant
    
    def delete_tenant(self, tenant_id: str, user_id: str) -> bool:
        """Delete tenant."""
        # Validate permissions
        if not self.validate_permissions(user_id, "delete", "tenant"):
            raise PermissionAPIError("Insufficient permissions to delete tenant")
        
        # Delete tenant
        result = self.repository.delete(tenant_id)
        
        # Log audit trail
        self.audit_log(
            action="delete",
            resource_type="tenant",
            resource_id=tenant_id,
            user_id=user_id
        )
        
        return result


# Initialize services
tenant_service = TenantService()


@router.get("/", response=PaginatedResponse)
def list_tenants(
    request: HttpRequest,
    filters: Query[BaseFilterSchema] = Query(...)
):
    """List all tenants with pagination and filtering."""
    try:
        result = tenant_service.repository.list(
            page=filters.page,
            page_size=filters.page_size,
            ordering=filters.ordering
        )
        
        return {
            "pagination": result["pagination"],
            "data": [TenantResponseSchema.from_orm(tenant) for tenant in result["data"]]
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to list tenants",
            "error": str(e)
        }, 500


@router.get("/{tenant_id}", response=TenantResponseSchema)
def get_tenant(request: HttpRequest, tenant_id: str):
    """Get tenant by ID."""
    try:
        tenant = tenant_service.repository.get_by_id(tenant_id)
        return TenantResponseSchema.from_orm(tenant)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get tenant",
            "error": str(e)
        }, 500


@router.post("/", response=TenantResponseSchema)
def create_tenant(request: HttpRequest, data: TenantCreateSchema):
    """Create a new tenant."""
    try:
        tenant = tenant_service.create_tenant(
            data.dict(),
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return TenantResponseSchema.from_orm(tenant)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create tenant",
            "error": str(e)
        }, 500


@router.put("/{tenant_id}", response=TenantResponseSchema)
def update_tenant(request: HttpRequest, tenant_id: str, data: TenantUpdateSchema):
    """Update existing tenant."""
    try:
        tenant = tenant_service.update_tenant(
            tenant_id,
            data.dict(exclude_unset=True),
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return TenantResponseSchema.from_orm(tenant)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to update tenant",
            "error": str(e)
        }, 500


@router.delete("/{tenant_id}")
def delete_tenant(request: HttpRequest, tenant_id: str):
    """Delete tenant."""
    try:
        result = tenant_service.delete_tenant(
            tenant_id,
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return {
            "success": True,
            "message": "Tenant deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to delete tenant",
            "error": str(e)
        }, 500


# Tenant Users endpoints
@router.get("/{tenant_id}/users", response=PaginatedResponse)
def list_tenant_users(
    request: HttpRequest,
    tenant_id: str,
    filters: Query[BaseFilterSchema] = Query(...)
):
    """List users for a specific tenant."""
    try:
        # TODO: Implement tenant user listing
        return {
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            },
            "data": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to list tenant users",
            "error": str(e)
        }, 500


@router.post("/{tenant_id}/users", response=TenantUserResponseSchema)
def add_tenant_user(
    request: HttpRequest,
    tenant_id: str,
    data: TenantUserCreateSchema
):
    """Add user to tenant."""
    try:
        # TODO: Implement add user to tenant
        return {
            "success": False,
            "message": "Not implemented yet"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to add user to tenant",
            "error": str(e)
        }, 500


# Tenant Invitations endpoints
@router.get("/{tenant_id}/invitations", response=PaginatedResponse)
def list_tenant_invitations(
    request: HttpRequest,
    tenant_id: str,
    filters: Query[BaseFilterSchema] = Query(...)
):
    """List invitations for a specific tenant."""
    try:
        # TODO: Implement tenant invitation listing
        return {
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            },
            "data": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to list tenant invitations",
            "error": str(e)
        }, 500


@router.post("/{tenant_id}/invitations", response=TenantInvitationResponseSchema)
def create_tenant_invitation(
    request: HttpRequest,
    tenant_id: str,
    data: TenantInvitationCreateSchema
):
    """Create invitation for tenant."""
    try:
        # TODO: Implement create tenant invitation
        return {
            "success": False,
            "message": "Not implemented yet"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create tenant invitation",
            "error": str(e)
        }, 500
