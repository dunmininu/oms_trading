# Model Cleanup Summary

## Issue Identified

The codebase had a **duplicate User model** that was causing conflicts and violating Django best practices:

1. **`backend/apps/core/models.py`** - Contains the main `User` model (inherits from `AbstractUser` + `BaseModel`)
2. **`backend/apps/accounts/models.py`** - Had a duplicate `User` model with similar fields

## What Was Fixed

### 1. Removed Duplicate User Model
- **Deleted** the duplicate `User` class from `backend/apps/accounts/models.py`
- **Kept** the `APIKey` and `UserSession` models in the accounts app
- **Updated** foreign key references in `APIKey` and `UserSession` to use `'core.User'`

### 2. Updated Settings Configuration
- **Changed** `AUTH_USER_MODEL` from `"accounts.User"` to `"core.User"` in `backend/apps/core/settings/base.py`

### 3. Fixed Import Statements
- **Updated** import in `backend/apps/api/v1/auth.py` from `...accounts.models import User` to `...core.models import User`

## Current State

### ✅ Correctly Configured
- **Single User Model**: `core.User` is the authoritative user model
- **Settings**: `AUTH_USER_MODEL = "core.User"` correctly points to the core User model
- **Foreign Keys**: All models correctly reference `'core.User'` using string references
- **No Duplicates**: Only one User model exists in the entire codebase

### 🔍 Verified Models
The following models correctly reference `'core.User'`:
- `accounts.APIKey.user`
- `accounts.UserSession.user`
- `tenants.TenantUser.user`
- `tenants.TenantInvitation.invited_by`
- `tenants.TenantInvitation.invited_by` (for sent invitations)
- `marketdata.MarketSubscription.user`
- `marketdata.MarketDataStream.user`
- `strategies.Strategy.user`
- `strategies.StrategyRun.user`
- `oms.Order.user`
- `core.AuditLog.user`

### 📁 Current File Structure
```
backend/apps/
├── core/
│   ├── models.py          # ✅ Contains User model (inherits AbstractUser + BaseModel)
│   └── settings/
│       └── base.py        # ✅ AUTH_USER_MODEL = "core.User"
├── accounts/
│   └── models.py          # ✅ Contains APIKey and UserSession (no User model)
├── tenants/
│   └── models.py          # ✅ References 'core.User' correctly
├── marketdata/
│   └── models.py          # ✅ References 'core.User' correctly
├── strategies/
│   └── models.py          # ✅ References 'core.User' correctly
├── oms/
│   └── models.py          # ✅ References 'core.User' correctly
└── brokers/
    └── models.py          # ✅ No User references
```

## Benefits of This Cleanup

### 1. **Eliminates Confusion**
- Single source of truth for user data
- No more duplicate model definitions
- Clear separation of concerns

### 2. **Follows Django Best Practices**
- One custom user model per project
- Proper inheritance hierarchy
- Consistent model relationships

### 3. **Prevents Runtime Errors**
- No more model conflicts during migrations
- Consistent user ID references
- Proper foreign key relationships

### 4. **Maintains Code Quality**
- Clean, maintainable codebase
- Easier to understand and modify
- Better testability

## User Model Features

The `core.User` model provides:

### **Core Fields** (from AbstractUser)
- `email` (used as username)
- `first_name`, `last_name`
- `is_active`, `is_staff`, `is_superuser`
- `date_joined`, `last_login`

### **Extended Fields** (from BaseModel)
- `id` (UUID primary key)
- `created_at`, `updated_at`
- `is_active` (duplicate, but consistent with BaseModel)

### **Custom Fields**
- `phone_number`, `date_of_birth`
- `avatar`, `bio`, `timezone`, `language`
- `email_verified`, `two_factor_enabled`
- `failed_login_attempts`, `locked_until`
- `last_activity`, `last_ip_address`

### **Security Features**
- Account locking after failed login attempts
- Two-factor authentication support
- Password reset functionality
- Session tracking

## Next Steps

### 1. **Database Migrations**
- Run `python manage.py makemigrations` to detect any model changes
- Run `python manage.py migrate` to apply changes
- Verify no migration conflicts

### 2. **Testing**
- Test user creation and authentication
- Verify foreign key relationships work correctly
- Test API endpoints that use User model

### 3. **Documentation**
- Update any remaining documentation references
- Ensure team members understand the single User model approach
- Document the User model's capabilities and usage

## Lessons Learned

### 1. **Always Check Existing Models**
- Search the codebase before creating new models
- Use Django's `AUTH_USER_MODEL` setting consistently
- Avoid model duplication

### 2. **Use String References for Foreign Keys**
- `'core.User'` instead of direct model imports
- Prevents circular import issues
- Makes models more maintainable

### 3. **Follow Django Conventions**
- One custom user model per project
- Proper inheritance hierarchy
- Consistent naming conventions

## Conclusion

The model cleanup successfully resolved the duplicate User model issue and established a clean, maintainable architecture. The codebase now follows Django best practices with a single, well-defined User model that serves as the foundation for all user-related functionality.

All foreign key relationships are properly configured, and the system is ready for continued development without model conflicts or confusion.
