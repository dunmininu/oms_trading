"""
Base classes for clean architecture implementation and API controller decorator.
"""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, Callable, Tuple

from django.db import models
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest
from django.apps import apps as django_apps

from .exceptions import (
    NotFoundAPIError,
    ValidationAPIError,
    PermissionAPIError,
    APIError,
)

T = TypeVar('T', bound=models.Model)


def api_controller(func: Callable) -> Callable:
    """Decorator to provide consistent auth/tenant injection and error handling.

    - Injects `tenant` and `user` from request if parameters exist
    - Catches APIError subclasses and returns structured error with HTTP code
    - Catches generic exceptions to avoid leaking internals
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Ninja passes request as first arg
        request: HttpRequest = args[0] if args else kwargs.get('request')

        # Inject user and tenant when function accepts them and request provides
        if 'user' in func.__code__.co_varnames and hasattr(request, 'user'):
            kwargs.setdefault('user', getattr(request, 'user', None))
        if 'tenant' in func.__code__.co_varnames:
            # Try to resolve and inject Tenant instance when possible
            tenant_value = kwargs.get('tenant')
            if tenant_value is None:
                # prefer already attached tenant object
                tenant_obj = getattr(request, 'tenant', None)
                if tenant_obj is None:
                    tenant_id_or_sub = getattr(request, 'tenant_id', None)
                    if tenant_id_or_sub:
                        try:
                            TenantModel = django_apps.get_model('tenants', 'Tenant')
                            try:
                                tenant_obj = TenantModel.objects.get(id=tenant_id_or_sub)
                            except Exception:
                                tenant_obj = TenantModel.objects.get(subdomain=tenant_id_or_sub)
                        except Exception:
                            tenant_obj = None
                if tenant_obj is not None:
                    kwargs['tenant'] = tenant_obj

        try:
            return func(*args, **kwargs)
        except APIError as api_err:
            return {
                "error": {
                    "code": api_err.code,
                    "message": api_err.message,
                    "type": api_err.error_type,
                }
            }, api_err.code
        except ValidationError as e:
            return {
                "error": {
                    "code": 400,
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e),
                }
            }, 400
        except Exception as e:
            return {
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "type": "internal_error",
                }
            }, 500

    return wrapper


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for data access."""

    def __init__(self, model: type[T]):
        self.model = model

    @abstractmethod
    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> T:
        """Get entity by ID with optional tenant filtering."""
        pass

    @abstractmethod
    def list(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List entities with pagination and filtering."""
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any], tenant_id: Optional[str] = None) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    def update(self, id: str, data: Dict[str, Any], tenant_id: Optional[str] = None) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete entity."""
        pass

    @abstractmethod
    def exists(self, id: str, tenant_id: Optional[str] = None) -> bool:
        """Check if entity exists."""
        pass


class DjangoRepository(BaseRepository[T]):
    """Django ORM implementation of base repository."""

    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> T:
        """Get entity by ID with optional tenant filtering."""
        try:
            queryset = self.model.objects.filter(id=id)
            if tenant_id and hasattr(self.model, 'tenant_id'):
                queryset = queryset.filter(tenant_id=tenant_id)

            return queryset.get()
        except ObjectDoesNotExist:
            raise NotFoundAPIError(f"{self.model.__name__} with id {id} not found")

    def list(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List entities with pagination and filtering."""
        queryset = self.model.objects.all()

        # Apply tenant filtering
        if tenant_id and hasattr(self.model, 'tenant_id'):
            queryset = queryset.filter(tenant_id=tenant_id)

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
            },
        }

    def create(self, data: Dict[str, Any], tenant_id: Optional[str] = None) -> T:
        """Create new entity."""
        if tenant_id and hasattr(self.model, 'tenant_id'):
            data['tenant_id'] = tenant_id

        try:
            instance = self.model.objects.create(**data)
            return instance
        except ValidationError as e:
            raise ValidationAPIError(f"Validation error: {e}")
        except Exception as e:
            raise ValidationAPIError(f"Error creating {self.model.__name__}: {e}")

    def update(self, id: str, data: Dict[str, Any], tenant_id: Optional[str] = None) -> T:
        """Update existing entity."""
        instance = self.get_by_id(id, tenant_id)

        try:
            for field, value in data.items():
                setattr(instance, field, value)
            instance.save()
            return instance
        except ValidationError as e:
            raise ValidationAPIError(f"Validation error: {e}")
        except Exception as e:
            raise ValidationAPIError(f"Error updating {self.model.__name__}: {e}")

    def delete(self, id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete entity."""
        instance = self.get_by_id(id, tenant_id)
        instance.delete()
        return True

    def exists(self, id: str, tenant_id: Optional[str] = None) -> bool:
        """Check if entity exists."""
        queryset = self.model.objects.filter(id=id)
        if tenant_id and hasattr(self.model, 'tenant_id'):
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset.exists()


class BaseUseCase(ABC):
    """Base use case interface for business logic."""

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the use case."""
        pass


class BaseService:
    """Base service class for business logic coordination."""

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    def validate_permissions(self, user, action: str, resource: Any = None) -> bool:
        """Validate user permissions for action."""
        # TODO: Implement permission validation
        return True

    def audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
    ):
        """Log audit trail for actions."""
        # TODO: Implement audit logging
        pass


class PaginationMixin:
    """Mixin for pagination functionality."""

    def paginate_queryset(self, queryset: QuerySet, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Paginate a queryset."""
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
            },
        }


class FilterMixin:
    """Mixin for filtering functionality."""

    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset."""
        for field, value in filters.items():
            if value is not None:
                if field.endswith('__in') and isinstance(value, str):
                    value = [v.strip() for v in value.split(',')]
                elif field.endswith('__icontains'):
                    queryset = queryset.filter(**{field: value})
                else:
                    queryset = queryset.filter(**{field: value})

        return queryset

    def apply_ordering(self, queryset: QuerySet, ordering: Optional[str] = None) -> QuerySet:
        """Apply ordering to queryset."""
        if ordering:
            if ordering.startswith('-'):
                field = ordering[1:]
                if hasattr(self.model, field):
                    queryset = queryset.order_by(ordering)
            else:
                if hasattr(self.model, ordering):
                    queryset = queryset.order_by(ordering)

        return queryset


class TenantMixin:
    """Mixin for tenant-aware operations."""

    def scope_to_tenant(self, queryset: QuerySet, tenant_id: str) -> QuerySet:
        """Scope queryset to specific tenant."""
        if hasattr(self.model, 'tenant_id'):
            return queryset.filter(tenant_id=tenant_id)
        return queryset

    def validate_tenant_access(self, user, tenant_id: str) -> bool:
        """Validate user has access to tenant."""
        # TODO: Implement tenant access validation
        return True
