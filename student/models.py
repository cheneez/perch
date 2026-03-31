from django.contrib.auth.models import User
from django.db import models

from accounts.profile_choices import GENDER_CHOICES

GRADE_YEAR_CHOICES = [
    ('ug_freshman', 'Undergraduate - Freshman'),
    ('ug_sophomore', 'Undergraduate - Sophomore'),
    ('ug_junior', 'Undergraduate - Junior'),
    ('ug_senior', 'Undergraduate - Senior'),
    ('grad_1', 'Graduate - 1st Year'),
    ('grad_2', 'Graduate - 2nd Year'),
    ('grad_3p', 'Graduate - 3rd Year+'),
    ('phd', 'PhD Student'),
    ('other', 'Other'),
]

EMPLOYMENT_CHOICES = [
    ('full_time', 'Employed full-time'),
    ('part_time', 'Employed part-time'),
    ('student', 'Student'),
    ('student_pt', 'Student with part-time job'),
    ('internship', 'Internship'),
    ('prefer_not', 'Prefer not to say'),
]

BUDGET_CHOICES = [
    ('under_800', 'Under $800'),
    ('800_1200', '$800–$1200'),
    ('1200_1600', '$1200–$1600'),
    ('1600_plus', '$1600+'),
]

HOBBY_TAG_OPTIONS = [
    ('gym', 'Gym'),
    ('gaming', 'Gaming'),
    ('cooking', 'Cooking'),
    ('reading', 'Reading'),
    ('music', 'Music'),
    ('hiking', 'Hiking'),
    ('sports', 'Sports'),
    ('movies', 'Movies'),
    ('art', 'Art'),
    ('traveling', 'Traveling'),
]


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
    )
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_type = models.CharField(max_length=20, default='Student', editable=False)
    date_of_birth = models.DateField(null=True, blank=True)
    school = models.CharField(max_length=200)
    grade_year = models.CharField(max_length=100, choices=GRADE_YEAR_CHOICES)
    gender_identity = models.CharField(max_length=100, choices=GENDER_CHOICES)
    gender_self_describe = models.CharField(max_length=200, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/students/',
        null=True,
        blank=True,
    )

    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=400, blank=True)
    fun_fact_1 = models.CharField(max_length=200, blank=True)
    fun_fact_2 = models.CharField(max_length=200, blank=True)
    fun_fact_3 = models.CharField(max_length=200, blank=True)

    hobbies = models.JSONField(default=list, blank=True)
    weekend_activities = models.TextField(max_length=300, blank=True)
    roommate_environment = models.TextField(max_length=300, blank=True)

    employment_status = models.CharField(
        max_length=100,
        choices=EMPLOYMENT_CHOICES,
        blank=True,
    )
    current_role = models.CharField(max_length=200, blank=True)
    housing_budget = models.CharField(
        max_length=50,
        choices=BUDGET_CHOICES,
        blank=True,
    )
    can_contribute_rent = models.BooleanField(null=True, blank=True)

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
        return f'StudentProfile({self.username})'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
