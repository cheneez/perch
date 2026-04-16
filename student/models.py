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

GRADUATION_YEAR_CHOICES = [
    ('2026', '2026'),
    ('2027', '2027'),
    ('2028', '2028'),
    ('2029', '2029'),
    ('2030', '2030'),
    ('2031_plus', '2031+'),
]

MAJOR_CHOICES = [
    ('cs', 'Computer Science'),
    ('business', 'Business'),
    ('economics', 'Economics'),
    ('biology', 'Biology'),
    ('psychology', 'Psychology'),
    ('nursing', 'Nursing'),
    ('engineering', 'Engineering'),
    ('political_science', 'Political Science'),
    ('communications', 'Communications'),
    ('english', 'English'),
    ('other', 'Other / Undecided'),
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

    hobbies = models.JSONField(default=list, blank=True)

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


class StudentCompatibilitySurvey(models.Model):
    """Single saved survey response per student user."""

    # Choice keys are prefixed with "s1_"..."s5_" so we can map to a 1–5 score.

    ROOMMATE_RELATIONSHIP_CHOICES = [
        ('s1_peaceful_coexist', 'I want to peacefully coexist (low interaction).'),
        ('s2_low', 'I like some interaction, but mostly independent.'),
        ('s3_balanced', 'Balanced — hang sometimes, do our own thing too.'),
        ('s4_social', 'I want a roommate who’s down to hang a lot.'),
        ('s5_everything_together', 'I want a roommate to do everything with.'),
    ]

    MORNING_NIGHT_PREF_CHOICES = [
        ('s5_morning_with_morning', 'I prefer to live with a morning person because I am a morning person.'),
        ('s4_morning_can_live_night', 'I can live with a night person even though I am a morning person.'),
        ('s2_night_can_live_morning', 'I can live with a morning person even though I am a night person.'),
        ('s1_night_with_night', 'I prefer to live with a night person because I am a night person.'),
    ]

    PERSONALITY_CHOICES = [
        ('s1_shy', 'Shy / reserved'),
        ('s2_fairly_shy', 'Fairly shy'),
        ('s3_in_between', 'Somewhere in between'),
        ('s4_fairly_outgoing', 'Fairly outgoing'),
        ('s5_outgoing', 'Outgoing / very social'),
    ]

    PETS_CHOICES = [
        ('s1_no_pets', 'No pets, please.'),
        ('s2_prefer_no', 'Prefer no pets.'),
        ('s3_depends', 'It depends on the pet.'),
        ('s4_okay', 'Okay with pets.'),
        ('s5_love_pets', 'Love pets / totally fine living with pets.'),
    ]

    SMOKING_CHOICES = [
        ('s1_no_smoking', 'No smoking.'),
        ('s2_outside_only', 'Only outside.'),
        ('s3_occasionally', 'Occasionally is okay.'),
        ('s4_okay', 'Okay with it.'),
        ('s5_doesnt_matter', 'Doesn’t matter to me.'),
    ]

    PARTY_AT_HOME_CHOICES = [
        ('s1_never', 'Never.'),
        ('s2_rarely', 'Rarely (special occasions).'),
        ('s3_sometimes', 'Sometimes.'),
        ('s4_often', 'Often.'),
        ('s5_very_often', 'Very often / love hosting.'),
    ]

    SLEEP_SCHEDULE_CHOICES = [
        ('s1_night_owl', 'Night owl (sleep late / wake late).'),
        ('s2_somewhat_late', 'Somewhat late schedule.'),
        ('s3_flexible', 'Flexible / varies.'),
        ('s4_somewhat_early', 'Somewhat early schedule.'),
        ('s5_early_riser', 'Early riser (sleep early / wake early).'),
    ]

    CLEANLINESS_CHOICES = [
        ('s1_messy', 'Messy / relaxed.'),
        ('s2_casual', 'Casual (some clutter is fine).'),
        ('s3_average', 'Average (clean up when needed).'),
        ('s4_neat', 'Neat (weekly cleaning).'),
        ('s5_very_neat', 'Very neat / organized.'),
    ]

    GUESTS_CHOICES = [
        ('s1_rare', 'Rarely.'),
        ('s2_sometimes', 'Sometimes.'),
        ('s3_weekends', 'Mostly on weekends.'),
        ('s4_few_times_week', 'A few times a week.'),
        ('s5_often', 'Often.'),
    ]

    NOISE_CHOICES = [
        ('s1_very_quiet', 'Very quiet home.'),
        ('s2_quiet', 'Mostly quiet.'),
        ('s3_moderate', 'Moderate noise is fine.'),
        ('s4_lively', 'Lively sometimes.'),
        ('s5_very_lively', 'Very lively / music and friends often.'),
    ]

    STUDY_AT_HOME_CHOICES = [
        ('s1_never', 'Never.'),
        ('s2_rarely', 'Rarely.'),
        ('s3_sometimes', 'Sometimes.'),
        ('s4_often', 'Often.'),
        ('s5_very_often', 'Very often.'),
    ]

    CONFLICT_STYLE_CHOICES = [
        ('s1_avoid', 'Prefer to avoid conflict.'),
        ('s2_text_first', 'Prefer texting first then talking.'),
        ('s3_calm', 'Talk it out calmly after cooling off.'),
        ('s4_direct', 'Talk it out directly.'),
        ('s5_immediate', 'Address it immediately and directly.'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='compatibility_survey',
    )

    graduation_year = models.CharField(max_length=20, choices=GRADUATION_YEAR_CHOICES)
    major = models.CharField(max_length=50, choices=MAJOR_CHOICES)
    pets = models.CharField(max_length=20, choices=PETS_CHOICES)
    smoking_habits = models.CharField(max_length=20, choices=SMOKING_CHOICES)
    party_at_home = models.CharField(max_length=20, choices=PARTY_AT_HOME_CHOICES)
    sleep_schedule = models.CharField(max_length=30, choices=SLEEP_SCHEDULE_CHOICES)
    roommate_relationship = models.CharField(max_length=30, choices=ROOMMATE_RELATIONSHIP_CHOICES)
    morning_night_preference = models.CharField(max_length=30, choices=MORNING_NIGHT_PREF_CHOICES)
    personality = models.CharField(max_length=30, choices=PERSONALITY_CHOICES)

    cleanliness = models.CharField(max_length=20, choices=CLEANLINESS_CHOICES)
    guests = models.CharField(max_length=20, choices=GUESTS_CHOICES)
    noise_level = models.CharField(max_length=20, choices=NOISE_CHOICES)
    study_at_home = models.CharField(max_length=20, choices=STUDY_AT_HOME_CHOICES)
    conflict_style = models.CharField(max_length=20, choices=CONFLICT_STYLE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'StudentCompatibilitySurvey(user_id={self.user_id})'

    def is_completed(self):
        """A survey is complete when all required response fields are present and scorable."""
        required_choice_fields = (
            'pets',
            'smoking_habits',
            'party_at_home',
            'sleep_schedule',
            'roommate_relationship',
            'morning_night_preference',
            'personality',
            'cleanliness',
            'guests',
            'noise_level',
            'study_at_home',
            'conflict_style',
        )
        if not self.graduation_year or not self.major:
            return False
        return all(self.score_from_choice(getattr(self, field, None)) is not None for field in required_choice_fields)

    @staticmethod
    def score_from_choice(value):
        """
        Expect keys like "s1_xxx"..."s5_xxx". Returns int 1..5 or None.
        """
        if not value:
            return None
        if isinstance(value, str) and value.startswith('s') and '_' in value:
            prefix = value.split('_', 1)[0]  # "s1"
            try:
                score = int(prefix[1:])
            except ValueError:
                return None
            if 1 <= score <= 5:
                return score
        return None
