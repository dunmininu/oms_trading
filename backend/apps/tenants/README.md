# Tenants App

The Tenants app provides comprehensive multi-tenancy support for the OMS Trading system. It allows multiple organizations (tenants) to use the same application instance while maintaining data isolation and role-based access control.

## Features

- **Multi-tenant Architecture**: Support for multiple organizations using the same system
- **Role-Based Access Control**: Granular permissions for different user roles
- **User Management**: Invite, manage, and control user access to tenants
- **Subscription Management**: Support for different subscription plans and limits
- **Business Information**: Comprehensive business and contact information storage
- **Trading Configuration**: Tenant-specific trading settings and limits

## Models

### Tenant

The main tenant entity representing an organization or trading firm.

**Key Fields:**
- Basic information (name, slug, display name, description)
- Contact information (email, phone, website, address)
- Business information (type, tax ID, registration number)
- Trading configuration (currency, timezone)
- Subscription and limits (plan, max users, max strategies, max orders)
- Status and settings (active, suspended, trial/subscription dates)

**Properties:**
- `is_trial_active`: Check if tenant is in trial period
- `is_subscription_active`: Check if tenant has active subscription
- `can_use_system`: Check if tenant can use the system

### TenantUser

Represents the relationship between users and tenants with role-based permissions.

**Key Fields:**
- Tenant and user references
- Role (OWNER, ADMIN, TRADER, VIEWER, ANALYST, RISK_MANAGER, COMPLIANCE)
- Permissions (can_trade, can_manage_users, can_manage_strategies, etc.)
- Status and invitation tracking

**Roles and Permissions:**
- **OWNER**: Full access to all features
- **ADMIN**: Full access except tenant deletion
- **TRADER**: Can trade and manage strategies
- **VIEWER**: Read-only access to reports
- **ANALYST**: Can view reports and analyze data
- **RISK_MANAGER**: Can manage risk settings and view reports
- **COMPLIANCE**: Can view reports for compliance purposes

### TenantInvitation

Manages the invitation system for adding users to tenants.

**Key Fields:**
- Tenant, email, and role
- Invitation token and expiration
- Status tracking (PENDING, ACCEPTED, DECLINED, EXPIRED)
- Email tracking (sent, opened, responded)

## API Endpoints

### Tenants

- `GET /api/tenants/` - List tenants (filtered by user membership)
- `POST /api/tenants/` - Create new tenant
- `GET /api/tenants/{id}/` - Get tenant details
- `PUT /api/tenants/{id}/` - Update tenant
- `DELETE /api/tenants/{id}/` - Delete tenant
- `GET /api/tenants/{id}/summary/` - Get tenant summary
- `GET /api/tenants/{id}/users/` - List tenant users
- `GET /api/tenants/{id}/invitations/` - List tenant invitations
- `POST /api/tenants/{id}/suspend/` - Suspend tenant
- `POST /api/tenants/{id}/activate/` - Activate suspended tenant

### Tenant Users

- `GET /api/tenant-users/` - List tenant users
- `POST /api/tenant-users/` - Add user to tenant
- `GET /api/tenant-users/{id}/` - Get tenant user details
- `PUT /api/tenant-users/{id}/` - Update tenant user
- `DELETE /api/tenant-users/{id}/` - Remove user from tenant
- `POST /api/tenant-users/{id}/activate/` - Activate user
- `POST /api/tenant-users/{id}/deactivate/` - Deactivate user
- `GET /api/tenant-users/my_memberships/` - Get current user's memberships

### Tenant Invitations

- `GET /api/tenant-invitations/` - List invitations
- `POST /api/tenant-invitations/` - Send invitation
- `GET /api/tenant-invitations/{id}/` - Get invitation details
- `PUT /api/tenant-invitations/{id}/` - Update invitation
- `DELETE /api/tenant-invitations/{id}/` - Delete invitation
- `POST /api/tenant-invitations/{id}/resend/` - Resend invitation
- `POST /api/tenant-invitations/{id}/respond/` - Accept/decline invitation
- `GET /api/tenant-invitations/my_invitations/` - Get invitations for current user
- `GET /api/tenant-invitations/pending/` - Get pending invitations for user's tenants

## Usage Examples

### Creating a Tenant

```python
from backend.apps.tenants.models import Tenant

tenant = Tenant.objects.create(
    name='My Trading Firm',
    slug='my-trading-firm',
    display_name='My Trading Firm LLC',
    contact_email='contact@mytradingfirm.com',
    business_type='LLC',
    default_currency='USD',
    timezone='America/New_York',
    subscription_plan='PROFESSIONAL',
    max_users=10,
    max_strategies=50,
    max_orders_per_day=5000
)
```

### Adding a User to a Tenant

```python
from backend.apps.tenants.models import TenantUser

tenant_user = TenantUser.objects.create(
    tenant=tenant,
    user=user,
    role='TRADER'
)
```

### Sending an Invitation

```python
from backend.apps.tenants.models import TenantInvitation
from django.utils import timezone
from datetime import timedelta

invitation = TenantInvitation.objects.create(
    tenant=tenant,
    email='newuser@example.com',
    role='TRADER',
    invited_by=current_user,
    expires_at=timezone.now() + timedelta(days=7)
)
```

### Accepting an Invitation

```python
# User accepts invitation
invitation.accept(user)

# This automatically creates a TenantUser record
```

## Permissions

The app includes comprehensive permission classes:

- **TenantPermission**: Controls access to tenant operations
- **TenantUserPermission**: Controls access to tenant user operations
- **TenantInvitationPermission**: Controls access to invitation operations
- **IsTenantMember**: Checks if user is a member of a specific tenant
- **IsTenantOwnerOrAdmin**: Checks if user is owner or admin of a tenant
- **IsTenantOwner**: Checks if user is owner of a tenant

## Configuration

### Settings

Add the following to your Django settings:

```python
INSTALLED_APPS = [
    # ... other apps
    'backend.apps.tenants',
]

# Tenant-specific settings
TENANT_DEFAULT_CURRENCY = 'USD'
TENANT_DEFAULT_TIMEZONE = 'UTC'
TENANT_DEFAULT_SUBSCRIPTION_PLAN = 'FREE'
TENANT_MAX_USERS_DEFAULT = 1
TENANT_MAX_STRATEGIES_DEFAULT = 5
TENANT_MAX_ORDERS_PER_DAY_DEFAULT = 100
```

### URLs

Include the tenant URLs in your main URL configuration:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('tenants/', include('backend.apps.tenants.urls')),
]
```

## Testing

Run the test suite:

```bash
python manage.py test backend.apps.tenants
```

The test suite covers:
- Model creation and validation
- Permission system
- Invitation workflow
- Integration scenarios
- Edge cases and error conditions

## Admin Interface

The app provides a comprehensive Django admin interface with:

- Tenant management with organized fieldsets
- User management with role-based permissions
- Invitation tracking and management
- Search and filtering capabilities
- Status indicators and color coding

## Signals

The app includes Django signals for:

- Cache invalidation on tenant changes
- Audit logging for tenant operations
- Automatic cleanup of related data

## Future Enhancements

- Email notification system for invitations
- Advanced billing and subscription management
- Tenant-specific branding and customization
- Multi-currency support
- Advanced analytics and reporting per tenant
- API rate limiting per tenant
- Tenant-specific feature flags

## Contributing

When contributing to the tenants app:

1. Follow Django best practices
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure proper permission handling
5. Consider multi-tenant implications for all changes

## Support

For questions or issues with the tenants app, please refer to the main project documentation or create an issue in the project repository.
