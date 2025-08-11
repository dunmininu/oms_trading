"""
Views for tenant models.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Tenant, TenantUser, TenantInvitation
from .serializers import (
    TenantSerializer, TenantCreateSerializer, TenantUpdateSerializer,
    TenantUserSerializer, TenantUserCreateSerializer, TenantUserUpdateSerializer,
    TenantInvitationSerializer, TenantInvitationCreateSerializer,
    TenantInvitationResponseSerializer, TenantSummarySerializer
)
from .permissions import (
    TenantPermission, TenantUserPermission, TenantInvitationPermission
)

User = get_user_model()


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for Tenant model."""
    
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'business_type', 'subscription_plan', 'is_active', 
        'is_suspended', 'country', 'default_currency'
    ]
    search_fields = ['name', 'display_name', 'contact_email', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return TenantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUpdateSerializer
        return TenantSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all tenants
        if user.is_superuser:
            return super().get_queryset()
        
        # Regular users can only see tenants they belong to
        return super().get_queryset().filter(
            tenant_users__user=user,
            tenant_users__is_active=True
        ).distinct()
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get tenant summary information."""
        tenant = self.get_object()
        serializer = TenantSummarySerializer(tenant)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get list of users for a specific tenant."""
        tenant = self.get_object()
        users = tenant.tenant_users.filter(is_active=True)
        serializer = TenantUserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invitations(self, request, pk=None):
        """Get list of invitations for a specific tenant."""
        tenant = self.get_object()
        invitations = tenant.invitations.all()
        serializer = TenantInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a tenant."""
        tenant = self.get_object()
        reason = request.data.get('reason', '')
        
        tenant.is_suspended = True
        tenant.suspension_reason = reason
        tenant.save()
        
        return Response({'status': 'Tenant suspended'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a suspended tenant."""
        tenant = self.get_object()
        
        tenant.is_suspended = False
        tenant.suspension_reason = ''
        tenant.save()
        
        return Response({'status': 'Tenant activated'})


class TenantUserViewSet(viewsets.ModelViewSet):
    """ViewSet for TenantUser model."""
    
    queryset = TenantUser.objects.all()
    serializer_class = TenantUserSerializer
    permission_classes = [IsAuthenticated, TenantUserPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'tenant', 'role', 'is_active', 'can_trade', 
        'can_manage_users', 'can_manage_strategies', 'can_manage_risk'
    ]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'tenant__name']
    ordering_fields = ['joined_at', 'role', 'user__email']
    ordering = ['-joined_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return TenantUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUserUpdateSerializer
        return TenantUserSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all tenant users
        if user.is_superuser:
            return super().get_queryset()
        
        # Regular users can only see tenant users for tenants they belong to
        return super().get_queryset().filter(
            tenant__tenant_users__user=user,
            tenant__tenant_users__is_active=True
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a tenant user."""
        tenant_user = self.get_object()
        
        tenant_user.is_active = False
        tenant_user.save()
        
        return Response({'status': 'User deactivated'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a deactivated tenant user."""
        tenant_user = self.get_object()
        
        tenant_user.is_active = True
        tenant_user.save()
        
        return Response({'status': 'User activated'})
    
    @action(detail=False, methods=['get'])
    def my_memberships(self, request):
        """Get current user's tenant memberships."""
        user = request.user
        memberships = TenantUser.objects.filter(
            user=user,
            is_active=True
        ).select_related('tenant')
        
        serializer = TenantUserSerializer(memberships, many=True)
        return Response(serializer.data)


class TenantInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for TenantInvitation model."""
    
    queryset = TenantInvitation.objects.all()
    serializer_class = TenantInvitationSerializer
    permission_classes = [IsAuthenticated, TenantInvitationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tenant', 'role', 'status', 'email']
    search_fields = ['email', 'tenant__name']
    ordering_fields = ['created_at', 'expires_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return TenantInvitationCreateSerializer
        return TenantInvitationSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all invitations
        if user.is_superuser:
            return super().get_queryset()
        
        # Regular users can only see invitations for tenants they belong to
        return super().get_queryset().filter(
            tenant__tenant_users__user=user,
            tenant__tenant_users__is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Set invited_by and expires_at when creating invitation."""
        serializer.save(
            invited_by=self.request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend an invitation."""
        invitation = self.get_object()
        
        if invitation.status != 'PENDING':
            return Response(
                {'error': 'Can only resend pending invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            return Response(
                {'error': 'Cannot resend expired invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend expiration by 7 days
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save()
        
        # Here you would typically send the email
        # For now, just return success
        return Response({'status': 'Invitation resent'})
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to an invitation (accept/decline)."""
        invitation = self.get_object()
        serializer = TenantInvitationResponseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            if action == 'accept':
                invitation.accept(request.user)
                return Response({'status': 'Invitation accepted'})
            elif action == 'decline':
                invitation.decline(notes)
                return Response({'status': 'Invitation declined'})
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_invitations(self, request):
        """Get invitations sent to current user's email."""
        user = request.user
        invitations = TenantInvitation.objects.filter(
            email=user.email,
            status='PENDING'
        ).select_related('tenant', 'invited_by')
        
        serializer = TenantInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending invitations for current user's tenants."""
        user = request.user
        pending_invitations = TenantInvitation.objects.filter(
            tenant__tenant_users__user=user,
            tenant__tenant_users__is_active=True,
            status='PENDING'
        ).select_related('tenant', 'invited_by')
        
        serializer = TenantInvitationSerializer(pending_invitations, many=True)
        return Response(serializer.data)
