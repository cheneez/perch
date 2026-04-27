import uuid
from datetime import date

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


def infer_admin_seed_user_type(user):
    """Pick a sensible default role for admin-created dev users."""
    if user.is_staff or user.is_superuser:
        return 'admin'
    email = (user.email or '').strip().lower()
    if email.endswith('@bc.edu'):
        return 'student'
    return 'realtor'


def ensure_account_profile(user, user_type=None, email_verified=None):
    """
    Ensure an auth User has an accounts.Profile row.

    Existing rows are only mutated when an explicit role/verification value is
    provided, or when staff/superusers must always remain admin.
    """
    desired_user_type = user_type or infer_admin_seed_user_type(user)
    if user.is_staff or user.is_superuser:
        desired_user_type = 'admin'

    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'user_type': desired_user_type},
    )

    updated_fields = []
    if (user.is_staff or user.is_superuser) and profile.user_type != 'admin':
        profile.user_type = 'admin'
        updated_fields.append('user_type')
    elif user_type is not None and profile.user_type != desired_user_type:
        profile.user_type = desired_user_type
        updated_fields.append('user_type')

    if email_verified is not None and profile.email_verified != email_verified:
        profile.email_verified = email_verified
        updated_fields.append('email_verified')

    if updated_fields:
        profile.save(update_fields=updated_fields)

    return profile


def ensure_student_profile(user):
    from student.models import StudentProfile

    default_first_name = (user.first_name or 'Test').strip() or 'Test'
    default_last_name = (user.last_name or 'Student').strip() or 'Student'

    student_profile, created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'username': user.username,
            'first_name': default_first_name,
            'last_name': default_last_name,
            'school': 'Boston College',
            'grade_year': 'ug_junior',
            'gender_identity': 'prefer_not',
            'email': user.email or '',
        },
    )

    updated_fields = []
    sync_fields = {
        'username': user.username,
        'first_name': default_first_name,
        'last_name': default_last_name,
    }
    for field_name, value in sync_fields.items():
        if getattr(student_profile, field_name) != value:
            setattr(student_profile, field_name, value)
            updated_fields.append(field_name)

    if not student_profile.email and user.email:
        student_profile.email = user.email
        updated_fields.append('email')
    if not student_profile.school:
        student_profile.school = 'Boston College'
        updated_fields.append('school')
    if not student_profile.grade_year:
        student_profile.grade_year = 'ug_junior'
        updated_fields.append('grade_year')
    if not student_profile.gender_identity:
        student_profile.gender_identity = 'prefer_not'
        updated_fields.append('gender_identity')

    if updated_fields and not created:
        student_profile.save(update_fields=updated_fields)

    return student_profile


def ensure_lessor_profile(user):
    from lessor.models import LessorProfile

    default_first_name = (user.first_name or 'Test').strip() or 'Test'
    default_last_name = (user.last_name or 'Lessor').strip() or 'Lessor'

    lessor_profile, created = LessorProfile.objects.get_or_create(
        user=user,
        defaults={
            'username': user.username,
            'first_name': default_first_name,
            'last_name': default_last_name,
            'email': user.email or '',
            'date_of_birth': date(2000, 1, 1),
            'gender_identity': 'prefer_not',
        },
    )

    updated_fields = []
    sync_fields = {
        'username': user.username,
        'first_name': default_first_name,
        'last_name': default_last_name,
    }
    for field_name, value in sync_fields.items():
        if getattr(lessor_profile, field_name) != value:
            setattr(lessor_profile, field_name, value)
            updated_fields.append(field_name)

    if not lessor_profile.email and user.email:
        lessor_profile.email = user.email
        updated_fields.append('email')
    if not lessor_profile.gender_identity:
        lessor_profile.gender_identity = 'prefer_not'
        updated_fields.append('gender_identity')
    if not lessor_profile.date_of_birth:
        lessor_profile.date_of_birth = date(2000, 1, 1)
        updated_fields.append('date_of_birth')

    if updated_fields and not created:
        lessor_profile.save(update_fields=updated_fields)

    return lessor_profile


def ensure_role_profile(user, profile=None):
    """
    Ensure the role-specific profile row exists for app visibility.

    Stale opposite-role rows are left intact intentionally to avoid deleting user
    data when an admin changes the account type.
    """
    profile = profile or ensure_account_profile(user)
    if profile.user_type == 'student':
        return ensure_student_profile(user)
    if profile.user_type in ('realtor', 'lessor'):
        return ensure_lessor_profile(user)
    return None
