"""
Serializers for tenant models.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import Tenant, TenantUser, TenantInvitation

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model in tenant context."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id', 'email']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""
    
    user_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'display_name', 'description',
            'contact_email', 'contact_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country',
            'business_type', 'tax_id', 'registration_number',
            'default_currency', 'timezone',
            'subscription_plan', 'max_users', 'max_strategies', 
            'max_orders_per_day', 'trial_ends_at', 'subscription_ends_at',
            'is_active', 'is_suspended', 'suspension_reason',
            'metadata', 'created_at', 'updated_at',
            'user_count', 'status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']
    
    def get_user_count(self, obj):
        """Get count of active users."""
        return obj.tenant_users.filter(is_active=True).count()
    
    def get_status(self, obj):
        """Get tenant status."""
        if obj.is_suspended:
            return 'suspended'
        elif not obj.is_active:
            return 'inactive'
        elif obj.is_trial_active:
            return 'trial'
        elif obj.is_subscription_active:
            return 'active'
        else:
            return 'expired'


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Tenant model."""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'display_name', 'description',
            'contact_email', 'contact_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country',
            'business_type', 'tax_id', 'registration_number',
            'default_currency', 'timezone',
            'subscription_plan', 'max_users', 'max_strategies', 
            'max_orders_per_day', 'trial_ends_at', 'subscription_ends_at',
            'metadata'
        ]
    
    def validate_slug(self, value):
        """Validate slug uniqueness."""
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError(_('A tenant with this slug already exists.'))
        return value
    
    def validate_name(self, value):
        """Validate name uniqueness."""
        if Tenant.objects.filter(name=value).exists():
            raise serializers.ValidationError(_('A tenant with this name already exists.'))
        return value


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Tenant model."""
    
    class Meta:
        model = Tenant
        fields = [
            'display_name', 'description',
            'contact_email', 'contact_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country',
            'business_type', 'tax_id', 'registration_number',
            'default_currency', 'timezone',
            'subscription_plan', 'max_users', 'max_strategies', 
            'max_orders_per_day', 'trial_ends_at', 'subscription_ends_at',
            'is_active', 'is_suspended', 'suspension_reason',
            'metadata'
        ]


class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser model."""
    
    user = UserSerializer(read_only=True)
    tenant = TenantSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'tenant', 'user', 'role',
            'can_trade', 'can_manage_users', 'can_manage_strategies',
            'can_view_reports', 'can_manage_risk',
            'is_active', 'joined_at', 'invited_by',
            'notification_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'joined_at']


class TenantUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TenantUser model."""
    
    class Meta:
        model = TenantUser
        fields = [
            'tenant', 'user', 'role',
            'can_trade', 'can_manage_users', 'can_manage_strategies',
            'can_view_reports', 'can_manage_risk',
            'notification_preferences'
        ]
    
    def validate(self, data):
        """Validate tenant user creation."""
        tenant = data['tenant']
        user = data['user']
        
        # Check if user is already a member of this tenant
        if TenantUser.objects.filter(tenant=tenant, user=user).exists():
            raise serializers.ValidationError(_('User is already a member of this tenant.'))
        
        # Check tenant limits
        if tenant.tenant_users.filter(is_active=True).count() >= tenant.max_users:
            raise serializers.ValidationError(_('Tenant has reached maximum user limit.'))
        
        return data


class TenantUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating TenantUser model."""
    
    class Meta:
        model = TenantUser
        fields = [
            'role',
            'can_trade', 'can_manage_users', 'can_manage_strategies',
            'can_view_reports', 'can_manage_risk',
            'is_active', 'notification_preferences'
        ]


class TenantInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TenantInvitation model."""
    
    tenant = TenantSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'tenant', 'email', 'role', 'invited_by',
            'token', 'expires_at', 'status',
            'responded_at', 'response_notes',
            'sent_at', 'opened_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'token', 'created_at', 'updated_at',
            'sent_at', 'opened_at', 'responded_at'
        ]


class TenantInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TenantInvitation model."""
    
    class Meta:
        model = TenantInvitation
        fields = ['tenant', 'email', 'role']
    
    def validate(self, data):
        """Validate invitation creation."""
        tenant = data['tenant']
        email = data['email']
        
        # Check if user is already a member
        if TenantUser.objects.filter(
            tenant=tenant, 
            user__email=email, 
            is_active=True
        ).exists():
            raise serializers.ValidationError(_('User is already a member of this tenant.'))
        
        # Check if invitation already exists
        if TenantInvitation.objects.filter(
            tenant=tenant, 
            email=email, 
            status='PENDING'
        ).exists():
            raise serializers.ValidationError(_('An invitation already exists for this email.'))
        
        # Check tenant limits
        if tenant.tenant_users.filter(is_active=True).count() >= tenant.max_users:
            raise serializers.ValidationError(_('Tenant has reached maximum user limit.'))
        
        return data


class TenantInvitationResponseSerializer(serializers.Serializer):
    """Serializer for responding to invitations."""
    
    action = serializers.ChoiceField(choices=['accept', 'decline'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        """Validate action choice."""
        if value not in ['accept', 'decline']:
            raise serializers.ValidationError(_('Invalid action. Must be accept or decline.'))
        return value


class TenantSummarySerializer(serializers.ModelSerializer):
    """Serializer for tenant summary information."""
    
    user_count = serializers.SerializerMethodField()
    active_strategies = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'display_name', 'business_type',
            'subscription_plan', 'is_active', 'is_suspended',
            'user_count', 'active_strategies', 'status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_count(self, obj):
        """Get count of active users."""
        return obj.tenant_users.filter(is_active=True).count()
    
    def get_active_strategies(self, obj):
        """Get count of active strategies."""
        # This would need to be implemented based on your strategies app
        return 0
    
    def get_status(self, obj):
        """Get tenant status."""
        if obj.is_suspended:
            return 'suspended'
        elif not obj.is_active:
            return 'inactive'
        elif obj.is_trial_active:
            return 'trial'
        elif obj.is_subscription_active:
            return 'active'
        else:
            return 'expired'
