import uuid

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'

    USER_TYPES = [
        ('student', 'Student'),
        ('realtor', 'Realtor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(blank=True, null=True, unique=True)
    verification_email_sent_at = models.DateTimeField(blank=True, null=True)
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    moderation_notes = models.TextField(blank=True)
    status_updated_at = models.DateTimeField(blank=True, null=True)
    status_updated_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='profile_status_updates',
    )

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
