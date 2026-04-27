from django.contrib import admin
from django.db.models import Count
from django.utils import timezone

from accounts.models import ensure_account_profile, ensure_role_profile
from .models import Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'price_monthly',
        'status',
        'moderation_status',
        'verified',
        'image_total',
        'created_at',
    )
    list_filter = ('moderation_status', 'status', 'verified', 'owner')
    search_fields = ('title', 'address', 'owner__username', 'owner__email')
    readonly_fields = ('verified', 'created_at', 'moderated_at', 'moderated_by')
    actions = ('approve_listings', 'reject_listings')
    inlines = (ListingImageInline,)

    fieldsets = (
        ('Listing', {'fields': ('owner', 'title', 'description', 'address')}),
        (
            'Details',
            {
                'fields': (
                    'price_monthly',
                    'room_type',
                    'lease_type',
                    'lease_start',
                    'lease_end',
                    'status',
                )
            },
        ),
        (
            'Moderation',
            {
                'fields': (
                    'moderation_status',
                    'moderation_notes',
                    'verified',
                    'moderated_at',
                    'moderated_by',
                )
            },
        ),
        ('System', {'fields': ('created_at',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner', 'moderated_by').annotate(
            image_count_total=Count('images')
        )

    @admin.display(description='Images', ordering='image_count_total')
    def image_total(self, obj):
        return getattr(obj, 'image_count_total', 0)

    @admin.action(description='Approve selected listings')
    def approve_listings(self, request, queryset):
        now = timezone.now()
        for listing in queryset:
            listing.moderation_status = Listing.ModerationStatus.APPROVED
            listing.moderated_at = now
            listing.moderated_by = request.user
            listing.save(
                update_fields=(
                    'moderation_status',
                    'moderated_at',
                    'moderated_by',
                    'verified',
                )
            )

    @admin.action(description='Reject selected listings')
    def reject_listings(self, request, queryset):
        now = timezone.now()
        for listing in queryset:
            listing.moderation_status = Listing.ModerationStatus.REJECTED
            listing.moderated_at = now
            listing.moderated_by = request.user
            listing.save(
                update_fields=(
                    'moderation_status',
                    'moderated_at',
                    'moderated_by',
                    'verified',
                )
            )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not (obj.owner.is_staff or obj.owner.is_superuser):
            profile = ensure_account_profile(
                obj.owner,
                user_type='realtor',
                email_verified=True,
            )
            ensure_role_profile(obj.owner, profile=profile)


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'uploaded_at')
    search_fields = ('listing__title', 'listing__address', 'listing__owner__username')
