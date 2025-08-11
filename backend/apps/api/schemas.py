"""
Common API schemas for Django Ninja.
"""

from ninja import Schema
from typing import Any, Dict, List, Optional, Union
from typing import Annotated
from datetime import datetime
from pydantic import Field


class ErrorResponse(Schema):
    """Standard error response schema."""
    
    error: Dict[str, Any] = Field(
        description="Error details",
        example={
            "code": 400,
            "message": "Validation error",
            "type": "validation_error",
            "details": {"field": "Field is required"}
        }
    )


class SuccessResponse(Schema):
    """Standard success response schema."""
    
    success: bool = Field(default=True, description="Success indicator")
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class PaginationSchema(Schema):
    """Pagination metadata schema."""
    
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_count: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(Schema):
    """Paginated response schema."""
    
    pagination: PaginationSchema = Field(description="Pagination metadata")
    data: List[Dict[str, Any]] = Field(description="List of items")


class HealthCheckResponse(Schema):
    """Health check response schema."""
    
    status: str = Field(description="Service status")
    service: str = Field(description="Service name")
    version: str = Field(description="API version")
    timestamp: datetime = Field(description="Check timestamp")
    checks: Dict[str, bool] = Field(description="Health check results")


class AuditLogSchema(Schema):
    """Audit log entry schema."""
    
    id: str = Field(description="Audit log entry ID")
    action: str = Field(description="Action performed")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: str = Field(description="ID of resource affected")
    user_id: Optional[str] = Field(description="User who performed the action")
    tenant_id: str = Field(description="Tenant context")
    ip_address: Optional[str] = Field(description="IP address of the request")
    user_agent: Optional[str] = Field(description="User agent of the request")
    old_values: Optional[Dict[str, Any]] = Field(description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(description="New values")
    created_at: datetime = Field(description="When the action was performed")


class IdempotencyKeySchema(Schema):
    """Idempotency key schema for request deduplication."""
    
    key: str = Field(description="Unique idempotency key")
    endpoint: str = Field(description="API endpoint")
    method: str = Field(description="HTTP method")
    expires_at: datetime = Field(description="When the key expires")


class RateLimitInfo(Schema):
    """Rate limit information schema."""
    
    limit: int = Field(description="Request limit per window")
    remaining: int = Field(description="Remaining requests in current window")
    reset_time: datetime = Field(description="When the rate limit resets")
    window_size: int = Field(description="Rate limit window size in seconds")


class APIResponse(Schema):
    """Generic API response wrapper."""
    
    success: bool = Field(description="Success indicator")
    data: Optional[Any] = Field(description="Response data")
    message: Optional[str] = Field(description="Response message")
    errors: Optional[List[str]] = Field(description="List of errors")
    warnings: Optional[List[str]] = Field(description="List of warnings")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# -----------------------------------------------------------------------------
# Compatibility Schemas expected by v1 endpoints
# -----------------------------------------------------------------------------

class ResponseSchema(Schema):
    """Simple success response used by endpoints like cancel_order."""

    success: bool = Field(default=True, description="Success indicator")
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class ErrorResponseSchema(ErrorResponse):
    """Alias for backward compatibility with code expecting ErrorResponseSchema."""

    pass


class PaginatedResponseSchema(PaginatedResponse):
    """Alias for backward compatibility with code expecting PaginatedResponseSchema."""

    pass


# Header type markers expected by endpoints. These subclass str so they can be
# passed directly to downstream services while still providing type clarity.
IdempotencyKeyHeader = Annotated[str, Field(description="Idempotency-Key header value")]


ETagHeader = Annotated[str, Field(description="If-Match/ETag header value")]


# Common field schemas
class IDSchema(Schema):
    """Common ID field schema."""
    
    id: str = Field(description="Unique identifier")


class TimestampSchema(Schema):
    """Common timestamp fields schema."""
    
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TenantSchema(Schema):
    """Common tenant field schema."""
    
    tenant_id: str = Field(description="Tenant identifier")


class UserSchema(Schema):
    """Common user field schema."""
    
    user_id: str = Field(description="User identifier")


class StatusSchema(Schema):
    """Common status field schema."""
    
    status: str = Field(description="Current status")
    status_reason: Optional[str] = Field(description="Reason for status change")


# Filter and search schemas
class BaseFilterSchema(Schema):
    """Base filter schema for list endpoints."""
    
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    page_size: Optional[int] = Field(default=20, ge=1, le=100, description="Page size")
    search: Optional[str] = Field(description="Search query")
    ordering: Optional[str] = Field(description="Ordering field (prefix with - for desc)")


class DateRangeFilterSchema(BaseFilterSchema):
    """Date range filter schema."""
    
    start_date: Optional[datetime] = Field(description="Start date for filtering")
    end_date: Optional[datetime] = Field(description="End date for filtering")


class StatusFilterSchema(BaseFilterSchema):
    """Status filter schema."""
    
    status: Optional[str] = Field(description="Filter by status")
    statuses: Optional[List[str]] = Field(description="Filter by multiple statuses")
