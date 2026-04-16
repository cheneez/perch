"""Create three local test student accounts (idempotent)."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from student.models import StudentProfile


TEST_STUDENTS = [
    {
        'username': 'test1',
        'email': 'test1@bc.edu',
        'first_name': 'Test',
        'last_name': 'One',
    },
    {
        'username': 'test2',
        'email': 'test2@bc.edu',
        'first_name': 'Test',
        'last_name': 'Two',
    },
    {
        'username': 'test3',
        'email': 'test3@bc.edu',
        'first_name': 'Test',
        'last_name': 'Three',
    },
]


class Command(BaseCommand):
    help = 'Create Test One / Two / Three student profiles for local dev (skips if usernames exist).'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for row in TEST_STUDENTS:
            if User.objects.filter(username=row['username']).exists():
                self.stdout.write(self.style.WARNING(f"Skip (exists): {row['username']}"))
                skipped += 1
                continue
            user = User.objects.create_user(
                username=row['username'],
                email=row['email'],
                password='testpass123',
                first_name=row['first_name'],
                last_name=row['last_name'],
            )
            Profile.objects.create(
                user=user,
                user_type='student',
                email_verified=True,
            )
            StudentProfile.objects.create(
                user=user,
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                school='Boston College',
                grade_year='ug_junior',
                gender_identity='prefer_not',
                email=row['email'],
            )
            self.stdout.write(self.style.SUCCESS(f"Created student: {row['username']} ({row['first_name']} {row['last_name']})"))
            created += 1
        self.stdout.write(
            f"Done. Created {created}, skipped {skipped}. Password for new users: testpass123"
        )
