"""
Tests for tenant models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import timedelta

from .models import Tenant, TenantUser, TenantInvitation

User = get_user_model()


class TenantModelTest(TestCase):
    """Test cases for Tenant model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.tenant_data = {
            'name': 'Test Trading Co',
            'slug': 'test-trading',
            'display_name': 'Test Trading Company',
            'description': 'A test trading company',
            'contact_email': 'contact@testtrading.com',
            'business_type': 'CORPORATION',
            'default_currency': 'USD',
            'timezone': 'America/New_York',
            'subscription_plan': 'PROFESSIONAL',
            'max_users': 10,
            'max_strategies': 20,
            'max_orders_per_day': 1000
        }
    
    def test_tenant_creation(self):
        """Test tenant creation with valid data."""
        tenant = Tenant.objects.create(**self.tenant_data)
        self.assertEqual(tenant.name, 'Test Trading Co')
        self.assertEqual(tenant.slug, 'test-trading')
        self.assertTrue(tenant.is_active)
        self.assertFalse(tenant.is_suspended)
    
    def test_tenant_unique_constraints(self):
        """Test tenant unique constraints."""
        Tenant.objects.create(**self.tenant_data)
        
        # Test duplicate name
        duplicate_name = self.tenant_data.copy()
        duplicate_name['slug'] = 'different-slug'
        with self.assertRaises(IntegrityError):
            Tenant.objects.create(**duplicate_name)
        
        # Test duplicate slug
        duplicate_slug = self.tenant_data.copy()
        duplicate_slug['name'] = 'Different Name'
        with self.assertRaises(IntegrityError):
            Tenant.objects.create(**duplicate_slug)
    
    def test_tenant_validation(self):
        """Test tenant validation logic."""
        # Test invalid currency format
        invalid_currency = self.tenant_data.copy()
        invalid_currency['default_currency'] = 'usd'  # lowercase
        
        tenant = Tenant(**invalid_currency)
        with self.assertRaises(ValidationError):
            tenant.full_clean()
    
    def test_tenant_properties(self):
        """Test tenant computed properties."""
        tenant = Tenant.objects.create(**self.tenant_data)
        
        # Test trial status
        self.assertFalse(tenant.is_trial_active)
        
        tenant.trial_ends_at = timezone.now() + timedelta(days=30)
        tenant.save()
        self.assertTrue(tenant.is_trial_active)
        
        # Test subscription status
        self.assertTrue(tenant.is_subscription_active)
        
        tenant.subscription_ends_at = timezone.now() - timedelta(days=1)
        tenant.save()
        self.assertFalse(tenant.is_subscription_active)
        
        # Test can_use_system
        self.assertFalse(tenant.can_use_system)
        
        tenant.subscription_ends_at = timezone.now() + timedelta(days=30)
        tenant.save()
        self.assertTrue(tenant.can_use_system)
    
    def test_tenant_clean_method(self):
        """Test tenant clean method validation."""
        tenant = Tenant(**self.tenant_data)
        tenant.trial_ends_at = timezone.now() + timedelta(days=30)
        tenant.subscription_ends_at = timezone.now() + timedelta(days=15)
        
        with self.assertRaises(ValidationError):
            tenant.clean()


class TenantUserModelTest(TestCase):
    """Test cases for TenantUser model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.tenant = Tenant.objects.create(
            name='Test Trading Co',
            slug='test-trading',
            display_name='Test Trading Company',
            contact_email='contact@testtrading.com',
            business_type='CORPORATION',
            default_currency='USD',
            max_users=5
        )
    
    def test_tenant_user_creation(self):
        """Test tenant user creation."""
        tenant_user = TenantUser.objects.create(
            tenant=self.tenant,
            user=self.user,
            role='TRADER'
        )
        
        self.assertEqual(tenant_user.tenant, self.tenant)
        self.assertEqual(tenant_user.user, self.user)
        self.assertEqual(tenant_user.role, 'TRADER')
        self.assertTrue(tenant_user.is_active)
    
    def test_tenant_user_unique_constraint(self):
        """Test tenant user unique constraint."""
        TenantUser.objects.create(
            tenant=self.tenant,
            user=self.user,
            role='TRADER'
        )
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            TenantUser.objects.create(
                tenant=self.tenant,
                user=self.user,
                role='ADMIN'
            )
    
    def test_tenant_user_permissions_by_role(self):
        """Test that permissions are set correctly based on role."""
        # Test OWNER role
        owner_user = TenantUser.objects.create(
            tenant=self.tenant,
            user=self.user,
            role='OWNER'
        )
        
        self.assertTrue(owner_user.can_trade)
        self.assertTrue(owner_user.can_manage_users)
        self.assertTrue(owner_user.can_manage_strategies)
        self.assertTrue(owner_user.can_view_reports)
        self.assertTrue(owner_user.can_manage_risk)
        
        # Test TRADER role
        trader_user = TenantUser.objects.create(
            tenant=self.tenant,
            user=User.objects.create_user(
                email='trader@example.com',
                password='testpass123'
            ),
            role='TRADER'
        )
        
        self.assertTrue(trader_user.can_trade)
        self.assertFalse(trader_user.can_manage_users)
        self.assertTrue(trader_user.can_manage_strategies)
        self.assertTrue(trader_user.can_view_reports)
        self.assertFalse(trader_user.can_manage_risk)
    
    def test_tenant_user_string_representation(self):
        """Test tenant user string representation."""
        tenant_user = TenantUser.objects.create(
            tenant=self.tenant,
            user=self.user,
            role='TRADER'
        )
        
        expected = f"{self.user.email} - {self.tenant.name} (TRADER)"
        self.assertEqual(str(tenant_user), expected)


class TenantInvitationModelTest(TestCase):
    """Test cases for TenantInvitation model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.tenant = Tenant.objects.create(
            name='Test Trading Co',
            slug='test-trading',
            display_name='Test Trading Company',
            contact_email='contact@testtrading.com',
            business_type='CORPORATION',
            default_currency='USD',
            max_users=5
        )
        
        self.invitation_data = {
            'tenant': self.tenant,
            'email': 'invite@example.com',
            'role': 'TRADER',
            'invited_by': self.user,
            'expires_at': timezone.now() + timedelta(days=7)
        }
    
    def test_invitation_creation(self):
        """Test invitation creation."""
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        
        self.assertEqual(invitation.tenant, self.tenant)
        self.assertEqual(invitation.email, 'invite@example.com')
        self.assertEqual(invitation.role, 'TRADER')
        self.assertEqual(invitation.status, 'PENDING')
        self.assertIsNotNone(invitation.token)
    
    def test_invitation_expiration(self):
        """Test invitation expiration logic."""
        # Test non-expired invitation
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        self.assertFalse(invitation.is_expired)
        
        # Test expired invitation
        expired_invitation = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='expired@example.com',
            role='TRADER',
            invited_by=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(expired_invitation.is_expired)
    
    def test_invitation_accept(self):
        """Test invitation acceptance."""
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        
        # Create user to accept invitation
        accepting_user = User.objects.create_user(
            email='invite@example.com',
            password='testpass123'
        )
        
        invitation.accept(accepting_user)
        
        # Check invitation status
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'ACCEPTED')
        self.assertIsNotNone(invitation.responded_at)
        
        # Check tenant user was created
        tenant_user = TenantUser.objects.get(
            tenant=self.tenant,
            user=accepting_user
        )
        self.assertEqual(tenant_user.role, 'TRADER')
        self.assertEqual(tenant_user.invited_by, self.user)
    
    def test_invitation_decline(self):
        """Test invitation decline."""
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        
        invitation.decline('Not interested')
        
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'DECLINED')
        self.assertIsNotNone(invitation.responded_at)
        self.assertEqual(invitation.response_notes, 'Not interested')
    
    def test_invitation_accept_expired(self):
        """Test that expired invitations cannot be accepted."""
        expired_invitation = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='expired@example.com',
            role='TRADER',
            invited_by=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        accepting_user = User.objects.create_user(
            email='expired@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(ValueError):
            expired_invitation.accept(accepting_user)
        
        expired_invitation.refresh_from_db()
        self.assertEqual(expired_invitation.status, 'EXPIRED')
    
    def test_invitation_accept_already_responded(self):
        """Test that responded invitations cannot be accepted again."""
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        invitation.status = 'ACCEPTED'
        invitation.save()
        
        accepting_user = User.objects.create_user(
            email='invite@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(ValueError):
            invitation.accept(accepting_user)
    
    def test_invitation_string_representation(self):
        """Test invitation string representation."""
        invitation = TenantInvitation.objects.create(**self.invitation_data)
        
        expected = f"Invitation to invite@example.com for {self.tenant.name}"
        self.assertEqual(str(invitation), expected)


class TenantIntegrationTest(TestCase):
    """Integration tests for tenant system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.tenant = Tenant.objects.create(
            name='Test Trading Co',
            slug='test-trading',
            display_name='Test Trading Company',
            contact_email='contact@testtrading.com',
            business_type='CORPORATION',
            default_currency='USD',
            max_users=3
        )
    
    def test_tenant_user_limit_enforcement(self):
        """Test that tenant user limits are enforced."""
        # Create users up to the limit
        for i in range(3):
            user = User.objects.create_user(
                email=f'user{i}@example.com',
                password='testpass123'
            )
            TenantUser.objects.create(
                tenant=self.tenant,
                user=user,
                role='TRADER'
            )
        
        # Try to add one more user
        extra_user = User.objects.create_user(
            email='extra@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(IntegrityError):
            TenantUser.objects.create(
                tenant=self.tenant,
                user=extra_user,
                role='TRADER'
            )
    
    def test_tenant_cascade_deletion(self):
        """Test that tenant deletion cascades properly."""
        # Create tenant users
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        TenantUser.objects.create(
            tenant=self.tenant,
            user=user1,
            role='TRADER'
        )
        TenantUser.objects.create(
            tenant=self.tenant,
            user=user2,
            role='ADMIN'
        )
        
        # Create invitations
        invitation1 = TenantInvitation.objects.create(
            tenant=self.tenant,
            email='invite1@example.com',
            role='TRADER',
            invited_by=user1,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Delete tenant
        self.tenant.delete()
        
        # Check that related objects were deleted
        self.assertEqual(TenantUser.objects.count(), 0)
        self.assertEqual(TenantInvitation.objects.count(), 0)
