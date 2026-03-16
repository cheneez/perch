import uuid

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    USER_TYPES = [
        ('student', 'Student'),
        ('realtor', 'Realtor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(blank=True, null=True, unique=True)
    verification_email_sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
