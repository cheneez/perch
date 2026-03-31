from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Report


def admin_change_url_for(obj):
    if obj is None:
        return None
    meta = obj._meta
    try:
        return reverse(f'admin:{meta.app_label}_{meta.model_name}_change', args=[obj.pk])
    except NoReverseMatch:
        return None


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reason',
        'status',
        'reporter',
        'admin_assignee',
        'target_link',
        'created_at',
    )
    list_filter = ('status', 'reason', 'content_type', 'admin_assignee')
    search_fields = ('reporter__username', 'reporter__email', 'details', 'resolution_notes')
    readonly_fields = ('content_type', 'object_id', 'target_link', 'created_at', 'updated_at', 'closed_at')
    actions = ('mark_in_review', 'mark_resolved', 'mark_dismissed')

    fieldsets = (
        (
            'Report',
            {
                'fields': (
                    'reporter',
                    'reason',
                    'details',
                    'status',
                    'admin_assignee',
                )
            },
        ),
        (
            'Target',
            {
                'fields': (
                    'content_type',
                    'object_id',
                    'target_link',
                )
            },
        ),
        (
            'Resolution',
            {
                'fields': (
                    'resolution_notes',
                    'created_at',
                    'updated_at',
                    'closed_at',
                )
            },
        ),
    )

    @admin.display(description='Target')
    def target_link(self, obj):
        target = obj.content_object
        if target is None:
            return format_html(
                '<span class="muted">{} #{}</span>',
                obj.content_type,
                obj.object_id,
            )
        url = admin_change_url_for(target)
        if url:
            return format_html('<a href="{}">{}</a>', url, target)
        return str(target)

    @admin.action(description='Mark selected reports in review')
    def mark_in_review(self, request, queryset):
        queryset.update(
            status=Report.Status.IN_REVIEW,
            admin_assignee=request.user,
            closed_at=None,
        )

    @admin.action(description='Resolve selected reports')
    def mark_resolved(self, request, queryset):
        queryset.update(
            status=Report.Status.RESOLVED,
            admin_assignee=request.user,
            closed_at=timezone.now(),
        )

    @admin.action(description='Dismiss selected reports')
    def mark_dismissed(self, request, queryset):
        queryset.update(
            status=Report.Status.DISMISSED,
            admin_assignee=request.user,
            closed_at=timezone.now(),
        )
