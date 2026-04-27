from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'kind', 'title', 'created_at', 'read_at')
    list_filter = ('kind', 'created_at', 'read_at')
    search_fields = ('recipient__username', 'recipient__email', 'title', 'body')
    readonly_fields = ('recipient', 'kind', 'title', 'body', 'link_url', 'created_at', 'read_at')

    def has_add_permission(self, request):
        return False

