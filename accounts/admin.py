from django.contrib import admin
from django.utils import timezone

from .models import Favorite, Profile


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorited_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'user__username',
        'favorited_user__username',
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'user_type',
        'account_status',
        'email_verified',
        'status_updated_at',
    )
    list_filter = ('user_type', 'account_status', 'email_verified')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = (
        'email_verification_token',
        'verification_email_sent_at',
        'status_updated_at',
        'status_updated_by',
    )
    actions = ('mark_suspended', 'mark_active')

    fieldsets = (
        ('Account', {'fields': ('user', 'user_type', 'email_verified')}),
        (
            'Moderation',
            {
                'fields': (
                    'account_status',
                    'moderation_notes',
                    'status_updated_at',
                    'status_updated_by',
                )
            },
        ),
        (
            'Verification',
            {'fields': ('email_verification_token', 'verification_email_sent_at')},
        ),
    )

    @admin.action(description='Mark selected users suspended')
    def mark_suspended(self, request, queryset):
        queryset.update(
            account_status=Profile.AccountStatus.SUSPENDED,
            status_updated_at=timezone.now(),
            status_updated_by=request.user,
        )

    @admin.action(description='Mark selected users active')
    def mark_active(self, request, queryset):
        queryset.update(
            account_status=Profile.AccountStatus.ACTIVE,
            status_updated_at=timezone.now(),
            status_updated_by=request.user,
        )
