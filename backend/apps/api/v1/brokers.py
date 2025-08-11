"""
Brokers API endpoints.
"""

from ninja import Router
from ninja import Query
from django.http import HttpRequest
from typing import Optional, List, Dict, Any

from ..schemas import (
    SuccessResponse, ErrorResponse, PaginatedResponse, 
    BaseFilterSchema, IDSchema, TimestampSchema, TenantSchema
)
from ..base import DjangoRepository, BaseService
from ...brokers.models import Broker, BrokerAccount
from ...brokers.schemas import (
    BrokerCreateSchema, BrokerUpdateSchema, BrokerResponseSchema,
    BrokerAccountCreateSchema, BrokerAccountUpdateSchema, BrokerAccountResponseSchema
)

router = Router(tags=["Broker Integration"])


class BrokerRepository(DjangoRepository[Broker]):
    """Repository for broker operations."""
    
    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> Broker:
        """Get broker by ID with tenant filtering."""
        try:
            queryset = self.model.objects.filter(id=id)
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
            return queryset.get()
        except Broker.DoesNotExist:
            raise NotFoundAPIError(f"Broker with id {id} not found")


class BrokerAccountRepository(DjangoRepository[BrokerAccount]):
    """Repository for broker account operations."""
    
    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> BrokerAccount:
        """Get broker account by ID with tenant filtering."""
        try:
            queryset = self.model.objects.filter(id=id)
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
            return queryset.get()
        except BrokerAccount.DoesNotExist:
            raise NotFoundAPIError(f"Broker account with id {id} not found")


class BrokerService(BaseService):
    """Service for broker business logic."""
    
    def __init__(self):
        super().__init__(BrokerRepository(Broker))
    
    def create_broker(self, data: Dict[str, Any], tenant_id: str, user_id: str) -> Broker:
        """Create a new broker."""
        # Validate permissions
        if not self.validate_permissions(user_id, "create", "broker"):
            raise PermissionAPIError("Insufficient permissions to create broker")
        
        # Add tenant_id to data
        data['tenant_id'] = tenant_id
        
        # Create broker
        broker = self.repository.create(data, tenant_id)
        
        # Log audit trail
        self.audit_log(
            action="create",
            resource_type="broker",
            resource_id=str(broker.id),
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return broker
    
    def update_broker(self, broker_id: str, data: Dict[str, Any], tenant_id: str, user_id: str) -> Broker:
        """Update existing broker."""
        # Validate permissions
        if not self.validate_permissions(user_id, "update", "broker"):
            raise PermissionAPIError("Insufficient permissions to update broker")
        
        # Update broker
        broker = self.repository.update(broker_id, data, tenant_id)
        
        # Log audit trail
        self.audit_log(
            action="update",
            resource_type="broker",
            resource_id=broker_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return broker
    
    def delete_broker(self, broker_id: str, tenant_id: str, user_id: str) -> bool:
        """Delete broker."""
        # Validate permissions
        if not self.validate_permissions(user_id, "delete", "broker"):
            raise PermissionAPIError("Insufficient permissions to delete broker")
        
        # Delete broker
        result = self.repository.delete(broker_id, tenant_id)
        
        # Log audit trail
        self.audit_log(
            action="delete",
            resource_type="broker",
            resource_id=broker_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return result


class BrokerAccountService(BaseService):
    """Service for broker account business logic."""
    
    def __init__(self):
        super().__init__(BrokerAccountRepository(BrokerAccount))
    
    def create_broker_account(self, data: Dict[str, Any], tenant_id: str, user_id: str) -> BrokerAccount:
        """Create a new broker account."""
        # Validate permissions
        if not self.validate_permissions(user_id, "create", "broker_account"):
            raise PermissionAPIError("Insufficient permissions to create broker account")
        
        # Add tenant_id to data
        data['tenant_id'] = tenant_id
        
        # Create broker account
        account = self.repository.create(data, tenant_id)
        
        # Log audit trail
        self.audit_log(
            action="create",
            resource_type="broker_account",
            resource_id=str(account.id),
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        return account


# Initialize services
broker_service = BrokerService()
broker_account_service = BrokerAccountService()


@router.get("/", response=PaginatedResponse)
def list_brokers(
    request: HttpRequest,
    filters: Query[BaseFilterSchema] = Query(...)
):
    """List all brokers for the current tenant."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        result = broker_service.repository.list(
            tenant_id=tenant_id,
            page=filters.page,
            page_size=filters.page_size,
            ordering=filters.ordering
        )
        
        return {
            "pagination": result["pagination"],
            "data": [BrokerResponseSchema.from_orm(broker) for broker in result["data"]]
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to list brokers",
            "error": str(e)
        }, 500


@router.get("/{broker_id}", response=BrokerResponseSchema)
def get_broker(request: HttpRequest, broker_id: str):
    """Get broker by ID."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        broker = broker_service.repository.get_by_id(broker_id, tenant_id)
        return BrokerResponseSchema.from_orm(broker)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get broker",
            "error": str(e)
        }, 500


@router.post("/", response=BrokerResponseSchema)
def create_broker(request: HttpRequest, data: BrokerCreateSchema):
    """Create a new broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        broker = broker_service.create_broker(
            data.dict(),
            tenant_id=tenant_id,
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return BrokerResponseSchema.from_orm(broker)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create broker",
            "error": str(e)
        }, 500


@router.put("/{broker_id}", response=BrokerResponseSchema)
def update_broker(request: HttpRequest, broker_id: str, data: BrokerUpdateSchema):
    """Update existing broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        broker = broker_service.update_broker(
            broker_id,
            data.dict(exclude_unset=True),
            tenant_id=tenant_id,
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return BrokerResponseSchema.from_orm(broker)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to update broker",
            "error": str(e)
        }, 500


@router.delete("/{broker_id}")
def delete_broker(request: HttpRequest, broker_id: str):
    """Delete broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        result = broker_service.delete_broker(
            broker_id,
            tenant_id=tenant_id,
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return {
            "success": True,
            "message": "Broker deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to delete broker",
            "error": str(e)
        }, 500


# Broker Accounts endpoints
@router.get("/{broker_id}/accounts", response=PaginatedResponse)
def list_broker_accounts(
    request: HttpRequest,
    broker_id: str,
    filters: Query[BaseFilterSchema] = Query(...)
):
    """List accounts for a specific broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        # TODO: Implement broker account listing
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
            "message": "Failed to list broker accounts",
            "error": str(e)
        }, 500


@router.post("/{broker_id}/accounts", response=BrokerAccountResponseSchema)
def create_broker_account(
    request: HttpRequest,
    broker_id: str,
    data: BrokerAccountCreateSchema
):
    """Create a new broker account."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        # Add broker_id to data
        account_data = data.dict()
        account_data['broker_id'] = broker_id
        
        account = broker_account_service.create_broker_account(
            account_data,
            tenant_id=tenant_id,
            user_id=str(request.user.id) if request.user.is_authenticated else None
        )
        return BrokerAccountResponseSchema.from_orm(account)
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create broker account",
            "error": str(e)
        }, 500


# Broker connection endpoints
@router.post("/{broker_id}/connect")
def connect_broker(request: HttpRequest, broker_id: str):
    """Connect to broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        # TODO: Implement broker connection logic
        return {
            "success": True,
            "message": "Broker connection initiated",
            "data": {
                "broker_id": broker_id,
                "status": "connecting"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to connect to broker",
            "error": str(e)
        }, 500


@router.post("/{broker_id}/disconnect")
def disconnect_broker(request: HttpRequest, broker_id: str):
    """Disconnect from broker."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        # TODO: Implement broker disconnection logic
        return {
            "success": True,
            "message": "Broker disconnection initiated",
            "data": {
                "broker_id": broker_id,
                "status": "disconnecting"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to disconnect from broker",
            "error": str(e)
        }, 500


@router.get("/{broker_id}/status")
def get_broker_status(request: HttpRequest, broker_id: str):
    """Get broker connection status."""
    try:
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {
                "success": False,
                "message": "Tenant context required",
                "error": "No tenant ID found in request"
            }, 400
        
        # TODO: Implement broker status checking
        return {
            "success": True,
            "data": {
                "broker_id": broker_id,
                "status": "disconnected",
                "last_connection": None,
                "connection_health": "unknown"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get broker status",
            "error": str(e)
        }, 500
