"""Create three local test lessor accounts (idempotent)."""

from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from lessor.models import LessorProfile


TEST_LESSORS = [
    {
        'username': 'test4',
        'email': 'test4@gmail.com',
        'first_name': 'Test',
        'last_name': 'Four',
    },
    {
        'username': 'test5',
        'email': 'test5@gmail.com',
        'first_name': 'Test',
        'last_name': 'Five',
    },
    {
        'username': 'test6',
        'email': 'test6@gmail.com',
        'first_name': 'Test',
        'last_name': 'Six',
    },
]


class Command(BaseCommand):
    help = 'Create Test Four / Five / Six lessor profiles for local dev (skips if usernames exist).'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for row in TEST_LESSORS:
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
                user_type='realtor',
                email_verified=True,
            )
            LessorProfile.objects.create(
                user=user,
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                date_of_birth=date(2000, 1, 1),
                gender_identity='prefer_not',
            )
            self.stdout.write(self.style.SUCCESS(f"Created lessor: {row['username']} ({row['first_name']} {row['last_name']})"))
            created += 1
        self.stdout.write(
            f"Done. Created {created}, skipped {skipped}. Password for new users: testpass123"
        )

