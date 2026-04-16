from django.contrib.auth.models import User
from django.db import models

from accounts.profile_choices import GENDER_CHOICES


class LessorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='leasor_profile',
    )
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_type = models.CharField(max_length=20, default='Lessor', editable=False)
    date_of_birth = models.DateField(null=True, blank=True)
    gender_identity = models.CharField(max_length=100, choices=GENDER_CHOICES)
    gender_self_describe = models.CharField(max_length=200, blank=True)
    verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to='profile_pics/leasors/',
        null=True,
        blank=True,
    )

    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=400, blank=True)

    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    handshake = models.URLField(blank=True)
    facebook = models.URLField(blank=True)

    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    show_instagram = models.BooleanField(default=True)
    show_linkedin = models.BooleanField(default=True)
    show_handshake = models.BooleanField(default=False)
    show_facebook = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'LessorProfile({self.username})'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
