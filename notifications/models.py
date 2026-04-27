from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        REPORT_RECEIVED = 'report_received', 'Report received'
        REPORT_UPDATED = 'report_updated', 'Report updated'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    kind = models.CharField(max_length=40, choices=Kind.choices)
    title = models.CharField(max_length=140)
    body = models.TextField(blank=True)
    link_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Notification({self.recipient_id}, {self.kind})'

