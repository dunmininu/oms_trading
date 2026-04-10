"""
Tenant schemas for API serialization.
"""

from datetime import datetime

from ninja import Schema
from pydantic import Field


class TenantCreateSchema(Schema):
    """Schema for creating a new tenant."""

    name: str = Field(..., description="Tenant name", max_length=100)
    slug: str = Field(..., description="Tenant slug", max_length=50)
    description: str | None = Field(
        None, description="Tenant description", max_length=500
    )
    domain: str | None = Field(None, description="Tenant domain")
    settings: dict | None = Field(default_factory=dict, description="Tenant settings")
    is_active: bool = Field(default=True, description="Whether tenant is active")


class TenantUpdateSchema(Schema):
    """Schema for updating a tenant."""

    name: str | None = Field(None, description="Tenant name", max_length=100)
    slug: str | None = Field(None, description="Tenant slug", max_length=50)
    description: str | None = Field(
        None, description="Tenant description", max_length=500
    )
    domain: str | None = Field(None, description="Tenant domain")
    settings: dict | None = Field(None, description="Tenant settings")
    is_active: bool | None = Field(None, description="Whether tenant is active")


class TenantResponseSchema(Schema):
    """Schema for tenant response."""

    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="Tenant slug")
    description: str | None = Field(None, description="Tenant description")
    domain: str | None = Field(None, description="Tenant domain")
    settings: dict = Field(default_factory=dict, description="Tenant settings")
    is_active: bool = Field(..., description="Whether tenant is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TenantUserCreateSchema(Schema):
    """Schema for adding a user to a tenant."""

    user_id: str = Field(..., description="User ID to add")
    role: str = Field(..., description="User role in tenant")
    permissions: list[str] | None = Field(
        default_factory=list, description="User permissions"
    )


class TenantUserUpdateSchema(Schema):
    """Schema for updating a tenant user."""

    role: str | None = Field(None, description="User role in tenant")
    permissions: list[str] | None = Field(None, description="User permissions")
    is_active: bool | None = Field(None, description="Whether user is active in tenant")


class TenantUserResponseSchema(Schema):
    """Schema for tenant user response."""

    id: str = Field(..., description="Tenant user ID")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    role: str = Field(..., description="User role")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    is_active: bool = Field(..., description="Whether user is active in tenant")
    joined_at: datetime = Field(..., description="When user joined tenant")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TenantInvitationCreateSchema(Schema):
    """Schema for creating a tenant invitation."""

    email: str = Field(..., description="Email to invite")
    role: str = Field(..., description="Role for invited user")
    permissions: list[str] | None = Field(
        default_factory=list, description="Permissions for invited user"
    )
    message: str | None = Field(None, description="Personal message for invitation")
    expires_at: datetime | None = Field(None, description="When invitation expires")


class TenantInvitationResponseSchema(Schema):
    """Schema for tenant invitation response."""

    id: str = Field(..., description="Invitation ID")
    tenant_id: str = Field(..., description="Tenant ID")
    email: str = Field(..., description="Invited email")
    role: str = Field(..., description="Role for invited user")
    permissions: list[str] = Field(
        default_factory=list, description="Permissions for invited user"
    )
    message: str | None = Field(None, description="Personal message for invitation")
    status: str = Field(..., description="Invitation status")
    expires_at: datetime | None = Field(None, description="When invitation expires")
    accepted_at: datetime | None = Field(
        None, description="When invitation was accepted"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
