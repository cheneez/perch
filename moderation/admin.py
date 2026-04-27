from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Report, ReportReply
from notifications.models import Notification


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
    list_display_links = ('id',)
    list_editable = ('status',)
    list_filter = ('status', 'reason', 'content_type', 'admin_assignee')
    search_fields = ('reporter__username', 'reporter__email', 'details', 'resolution_notes')
    readonly_fields = (
        'reporter',
        'reason',
        'details',
        'content_type',
        'object_id',
        'target_link',
        'created_at',
        'updated_at',
        'closed_at',
    )
    actions = ('mark_in_review', 'mark_resolved', 'mark_dismissed')
    inlines = ()

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

    class ReportReplyInline(admin.TabularInline):
        model = ReportReply
        fields = ('created_at', 'sender', 'message')
        readonly_fields = ('created_at', 'sender')
        extra = 1

    inlines = (ReportReplyInline,)

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
        for obj in queryset.select_related('reporter'):
            self._notify_reporter_update(
                obj,
                kind='status',
                new_status=Report.Status.IN_REVIEW,
            )
        queryset.update(status=Report.Status.IN_REVIEW, admin_assignee=request.user, closed_at=None)

    @admin.action(description='Resolve selected reports')
    def mark_resolved(self, request, queryset):
        for obj in queryset.select_related('reporter'):
            self._notify_reporter_update(
                obj,
                kind='status',
                new_status=Report.Status.RESOLVED,
            )
        queryset.update(status=Report.Status.RESOLVED, admin_assignee=request.user, closed_at=timezone.now())

    @admin.action(description='Dismiss selected reports')
    def mark_dismissed(self, request, queryset):
        for obj in queryset.select_related('reporter'):
            self._notify_reporter_update(
                obj,
                kind='status',
                new_status=Report.Status.DISMISSED,
            )
        queryset.update(status=Report.Status.DISMISSED, admin_assignee=request.user, closed_at=timezone.now())

    def save_model(self, request, obj, form, change):
        old_status = None
        old_notes = None
        if change and obj.pk:
            prev = Report.objects.filter(pk=obj.pk).only('status', 'resolution_notes').first()
            if prev:
                old_status = prev.status
                old_notes = prev.resolution_notes or ''

        super().save_model(request, obj, form, change)

        if not change:
            return

        new_status = obj.status
        new_notes = (obj.resolution_notes or '')
        if old_status is not None and new_status != old_status:
            self._notify_reporter_update(obj, kind='status', new_status=new_status)
        elif old_notes is not None and new_notes != old_notes:
            self._notify_reporter_update(
                obj,
                kind='notes',
                new_status=None,
                note_excerpt=new_notes,
            )

    def _notify_reporter_update(self, obj, kind, new_status=None, note_excerpt=None):
        reporter = getattr(obj, 'reporter', None)
        if not reporter:
            return
        if kind == 'status' and new_status:
            status_label = Report.Status(new_status).label if new_status in Report.Status.values else str(new_status)
            title = 'Report updated'
            body = f'An admin updated your report status to “{status_label}”.'
        else:
            title = 'Report updated'
            excerpt = (note_excerpt or '').strip()
            if excerpt:
                if len(excerpt) > 500:
                    excerpt = excerpt[:500].rstrip() + '…'
                body = excerpt
            else:
                body = 'An admin added an update to your report.'

        Notification.objects.create(
            recipient=reporter,
            kind=Notification.Kind.REPORT_UPDATED,
            title=title,
            body=body,
            link_url='/notifications/',
        )

    def save_formset(self, request, form, formset, change):
        if getattr(formset, 'model', None) is ReportReply:
            instances = formset.save(commit=False)
            for inst in instances:
                if not inst.sender_id:
                    inst.sender = request.user
                inst.save()
                # Notify reporter on new reply.
                report = inst.report
                reporter = getattr(report, 'reporter', None)
                if reporter:
                    Notification.objects.create(
                        recipient=reporter,
                        kind=Notification.Kind.REPORT_UPDATED,
                        title='Admin replied to your report',
                        body=inst.message[:500],
                        link_url='/notifications/',
                    )
            formset.save_m2m()
            return
        return super().save_formset(request, form, formset, change)
