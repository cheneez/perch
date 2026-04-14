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
        ('admin', 'Admin'),
    ]

    @staticmethod
    def default_user_type_for_user(user):
        """Account type for a new Profile row; staff are never defaulted to student."""
        if user.is_staff or user.is_superuser:
            return 'admin'
        return 'student'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPES,
        default='student',
    )
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


def get_or_create_account_profile(user, default_role_when_not_staff='student'):
    """Return (profile, created). Staff always get admin on create; others use default_role_when_not_staff."""
    inferred = Profile.default_user_type_for_user(user)
    create_type = 'admin' if inferred == 'admin' else default_role_when_not_staff
    return Profile.objects.get_or_create(
        user=user,
        defaults={'user_type': create_type},
    )


class Favorite(models.Model):
    """Viewer-saved profile owner for a future Favorites listing page."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites_made',
    )
    favorited_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'favorited_user'),
                name='accounts_favorite_user_favorited_user_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.user_id} -> {self.favorited_user_id}'
