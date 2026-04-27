from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Profile, ensure_account_profile

from .models import LessorProfile, VerificationRequest


class LessorUserAdminForm(forms.ModelForm):
    username = forms.CharField(help_text='Used for login and public profile URLs.')
    email = forms.EmailField(help_text='Used for login and contact defaults.')
    password1 = forms.CharField(
        required=False,
        label='Password',
        widget=forms.PasswordInput(render_value=False),
    )
    password2 = forms.CharField(
        required=False,
        label='Password confirmation',
        widget=forms.PasswordInput(render_value=False),
    )
    email_verified = forms.BooleanField(required=False, initial=True)
    account_status = forms.ChoiceField(
        choices=Profile.AccountStatus.choices,
        initial=Profile.AccountStatus.ACTIVE,
    )
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = LessorProfile
        fields = (
            'first_name',
            'last_name',
            'gender_identity',
            'is_verified',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'gender_identity' in self.fields:
            self.fields['gender_identity'].required = False
        if 'is_verified' in self.fields:
            self.fields['is_verified'].required = False

        if self.instance.pk and self.instance.user_id:
            user = self.instance.user
            profile = Profile.objects.filter(user=user).first()
            if 'username' in self.fields:
                self.fields['username'].initial = user.username
            if 'email' in self.fields:
                self.fields['email'].initial = user.email
            if 'is_active' in self.fields:
                self.fields['is_active'].initial = user.is_active
            if profile:
                if 'email_verified' in self.fields:
                    self.fields['email_verified'].initial = profile.email_verified
                if 'account_status' in self.fields:
                    self.fields['account_status'].initial = profile.account_status

        if 'gender_identity' in self.fields:
            self.fields['gender_identity'].initial = (
                self.fields['gender_identity'].initial or 'prefer_not'
            )
        if 'is_verified' in self.fields:
            self.fields['is_verified'].initial = (
                self.fields['is_verified'].initial if self.fields['is_verified'].initial is not None else True
            )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('That email is already in use.')
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1') or ''
        password2 = cleaned.get('password2') or ''
        if not self.instance.pk and not password1:
            self.add_error('password1', 'Password is required.')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
            else:
                password_user = self.instance.user if self.instance.pk and self.instance.user_id else User()
                password_user.username = cleaned.get('username', '')
                password_user.email = cleaned.get('email', '')
                password_user.first_name = cleaned.get('first_name', '')
                password_user.last_name = cleaned.get('last_name', '')
                try:
                    validate_password(password1, password_user)
                except ValidationError as exc:
                    self.add_error('password1', exc)
        return cleaned


class LessorUserAddForm(LessorUserAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('email_verified', 'account_status', 'is_active'):
            self.fields.pop(field_name, None)


@admin.register(LessorProfile)
class LessorUserAdmin(admin.ModelAdmin):
    form = LessorUserAdminForm
    list_display = (
        'username',
        'first_name',
        'last_name',
        'lessor_email',
        'email_verified_display',
        'account_status_display',
        'user_is_active',
    )
    search_fields = ('username', 'first_name', 'last_name', 'user__email')
    list_select_related = ('user', 'user__profile')

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'user__profile')
            .filter(user__profile__user_type='realtor')
        )

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = LessorUserAddForm if obj is None else self.form
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (
                    'Account',
                    {
                        'fields': (
                            'username',
                            'email',
                            'password1',
                            'password2',
                        )
                    },
                ),
                (
                    'Lessor profile',
                    {
                        'fields': (
                            'first_name',
                            'last_name',
                        )
                    },
                ),
            )
        return (
            (
                'Account',
                {
                    'fields': (
                        'username',
                        'email',
                        'password1',
                        'password2',
                        'is_active',
                        'email_verified',
                        'account_status',
                    )
                },
            ),
            (
                'Lessor profile',
                {
                    'fields': (
                        'first_name',
                        'last_name',
                        'gender_identity',
                        'is_verified',
                    )
                },
            ),
        )

    @admin.display(description='Email')
    def lessor_email(self, obj):
        return obj.user.email

    @admin.display(boolean=True, description='Verified')
    def email_verified_display(self, obj):
        return obj.user.profile.email_verified

    @admin.display(description='Status')
    def account_status_display(self, obj):
        return obj.user.profile.account_status

    @admin.display(boolean=True, description='Login enabled')
    def user_is_active(self, obj):
        return obj.user.is_active

    def save_model(self, request, obj, form, change):
        cleaned = form.cleaned_data

        if change and obj.user_id:
            user = obj.user
        else:
            user = User()

        user.username = cleaned['username']
        user.email = cleaned['email']
        user.first_name = cleaned['first_name']
        user.last_name = cleaned['last_name']
        user.is_active = cleaned.get('is_active', True)

        password = cleaned.get('password1')
        if password:
            user.set_password(password)

        user.save()

        obj.user = user
        obj.username = cleaned['username']
        obj.email = cleaned['email']
        obj.gender_identity = cleaned.get('gender_identity') or 'prefer_not'
        obj.is_verified = cleaned.get('is_verified', True)
        super().save_model(request, obj, form, change)

        profile = ensure_account_profile(
            user,
            user_type='realtor',
            email_verified=cleaned.get('email_verified', True),
        )
        desired_status = cleaned.get('account_status', Profile.AccountStatus.ACTIVE)
        if profile.account_status != desired_status:
            profile.account_status = desired_status
            profile.status_updated_at = timezone.now()
            profile.status_updated_by = request.user
            profile.save(
                update_fields=(
                    'account_status',
                    'status_updated_at',
                    'status_updated_by',
                )
            )


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('lessor_name', 'lessor_email', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('lessor__first_name', 'lessor__last_name', 'lessor__user__email')
    readonly_fields = (
        'lessor',
        'submitted_at',
        'reviewed_at',
        'reviewed_by',
        'government_id_link',
        'property_proof_link',
    )
    fields = (
        'lessor',
        'submitted_at',
        'government_id_link',
        'property_proof_link',
        'status',
        'admin_feedback',
        'reviewed_at',
        'reviewed_by',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lessor', 'lessor__user', 'reviewed_by')

    @admin.display(description='Lessor')
    def lessor_name(self, obj):
        return obj.lessor.full_name() or obj.lessor.username

    @admin.display(description='Email')
    def lessor_email(self, obj):
        return obj.lessor.user.email

    @admin.display(description='Government ID')
    def government_id_link(self, obj):
        from django.utils.html import format_html
        if obj.government_id:
            return format_html('<a href="{}" target="_blank">View / Download</a>', obj.government_id.url)
        return '—'

    @admin.display(description='Property Proof')
    def property_proof_link(self, obj):
        from django.utils.html import format_html
        if obj.property_proof:
            return format_html('<a href="{}" target="_blank">View / Download</a>', obj.property_proof.url)
        return '—'

    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            original_status = VerificationRequest.objects.filter(pk=obj.pk).values_list('status', flat=True).first()
        else:
            original_status = None

        status_changed = original_status != obj.status
        if status_changed and obj.status in (VerificationRequest.Status.VERIFIED, VerificationRequest.Status.DECLINED):
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user

        super().save_model(request, obj, form, change)

        if status_changed:
            if obj.status == VerificationRequest.Status.VERIFIED:
                obj.lessor.is_verified = True
                obj.lessor.save(update_fields=['is_verified'])
            elif obj.status == VerificationRequest.Status.DECLINED:
                obj.lessor.is_verified = False
                obj.lessor.save(update_fields=['is_verified'])
