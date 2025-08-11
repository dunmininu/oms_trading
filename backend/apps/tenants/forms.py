"""
Forms for tenant models.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

from .models import Tenant, TenantUser, TenantInvitation

User = get_user_model()


class TenantForm(forms.ModelForm):
    """Form for creating/editing Tenant model."""
    
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
            'is_active', 'is_suspended', 'suspension_reason',
            'metadata'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'suspension_reason': forms.Textarea(attrs={'rows': 3}),
            'metadata': forms.Textarea(attrs={'rows': 3}),
            'trial_ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'subscription_ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean_slug(self):
        """Validate slug uniqueness."""
        slug = self.cleaned_data['slug']
        instance = getattr(self, 'instance', None)
        
        if Tenant.objects.filter(slug=slug).exclude(pk=instance.pk if instance else None).exists():
            raise forms.ValidationError(_('A tenant with this slug already exists.'))
        
        return slug
    
    def clean_name(self):
        """Validate name uniqueness."""
        name = self.cleaned_data['name']
        instance = getattr(self, 'instance', None)
        
        if Tenant.objects.filter(name=name).exclude(pk=instance.pk if instance else None).exists():
            raise forms.ValidationError(_('A tenant with this name already exists.'))
        
        return name
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        trial_ends_at = cleaned_data.get('trial_ends_at')
        subscription_ends_at = cleaned_data.get('subscription_ends_at')
        
        if trial_ends_at and subscription_ends_at:
            if trial_ends_at > subscription_ends_at:
                raise forms.ValidationError(
                    _('Trial end date cannot be after subscription end date.')
                )
        
        return cleaned_data


class TenantUserForm(forms.ModelForm):
    """Form for creating/editing TenantUser model."""
    
    class Meta:
        model = TenantUser
        fields = [
            'tenant', 'user', 'role',
            'can_trade', 'can_manage_users', 'can_manage_strategies',
            'can_view_reports', 'can_manage_risk',
            'is_active', 'notification_preferences'
        ]
        widgets = {
            'notification_preferences': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        tenant = cleaned_data.get('tenant')
        user = cleaned_data.get('user')
        instance = getattr(self, 'instance', None)
        
        if tenant and user:
            # Check if user is already a member of this tenant
            existing = TenantUser.objects.filter(
                tenant=tenant, 
                user=user
            ).exclude(pk=instance.pk if instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    _('User is already a member of this tenant.')
                )
            
            # Check tenant limits
            if not instance or instance.tenant != tenant:
                if tenant.tenant_users.filter(is_active=True).count() >= tenant.max_users:
                    raise forms.ValidationError(
                        _('Tenant has reached maximum user limit.')
                    )
        
        return cleaned_data


class TenantInvitationForm(forms.ModelForm):
    """Form for creating/editing TenantInvitation model."""
    
    class Meta:
        model = TenantInvitation
        fields = [
            'tenant', 'email', 'role', 'invited_by',
            'expires_at', 'status', 'response_notes'
        ]
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'response_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        tenant = cleaned_data.get('tenant')
        email = cleaned_data.get('email')
        instance = getattr(self, 'instance', None)
        
        if tenant and email:
            # Check if user is already a member
            if TenantUser.objects.filter(
                tenant=tenant, 
                user__email=email, 
                is_active=True
            ).exists():
                raise forms.ValidationError(
                    _('User is already a member of this tenant.')
                )
            
            # Check if invitation already exists
            existing = TenantInvitation.objects.filter(
                tenant=tenant, 
                email=email, 
                status='PENDING'
            ).exclude(pk=instance.pk if instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    _('An invitation already exists for this email.')
                )
            
            # Check tenant limits
            if not instance or instance.tenant != tenant:
                if tenant.tenant_users.filter(is_active=True).count() >= tenant.max_users:
                    raise forms.ValidationError(
                        _('Tenant has reached maximum user limit.')
                    )
        
        return cleaned_data


class TenantInvitationResponseForm(forms.Form):
    """Form for responding to invitations."""
    
    action = forms.ChoiceField(
        choices=[('accept', 'Accept'), ('decline', 'Decline')],
        widget=forms.RadioSelect
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text=_('Optional notes for declining the invitation.')
    )
    
    def clean_notes(self):
        """Validate notes field."""
        action = self.cleaned_data.get('action')
        notes = self.cleaned_data.get('notes')
        
        if action == 'decline' and not notes:
            raise forms.ValidationError(
                _('Please provide a reason for declining the invitation.')
            )
        
        return notes


class TenantSearchForm(forms.Form):
    """Form for searching tenants."""
    
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search tenants...'),
            'class': 'form-control'
        })
    )
    
    business_type = forms.ChoiceField(
        required=False,
        choices=[('', _('All Business Types'))] + Tenant._meta.get_field('business_type').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    subscription_plan = forms.ChoiceField(
        required=False,
        choices=[('', _('All Plans'))] + Tenant._meta.get_field('subscription_plan').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Statuses')),
            ('active', _('Active')),
            ('suspended', _('Suspended')),
            ('inactive', _('Inactive')),
            ('trial', _('Trial')),
            ('expired', _('Expired'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    country = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Country'),
            'class': 'form-control'
        })
    )


class TenantUserSearchForm(forms.Form):
    """Form for searching tenant users."""
    
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search users...'),
            'class': 'form-control'
        })
    )
    
    role = forms.ChoiceField(
        required=False,
        choices=[('', _('All Roles'))] + TenantUser._meta.get_field('role').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Statuses')),
            ('active', _('Active')),
            ('inactive', _('Inactive'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    can_trade = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Trading Permissions')),
            ('true', _('Can Trade')),
            ('false', _('Cannot Trade'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
