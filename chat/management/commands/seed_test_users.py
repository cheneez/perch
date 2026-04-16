import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile


TEST_STUDENTS = [
    {
        'username': 'teststudent1',
        'email': 'teststudent1@bc.edu',
        'first_name': 'Test',
        'last_name': 'Student',
        'password': 'testpass123',
    },
    {
        'username': 'teststudent2',
        'email': 'teststudent2@bc.edu',
        'first_name': 'Demo',
        'last_name': 'User',
        'password': 'testpass123',
    },
]


class Command(BaseCommand):
    help = 'Create test student accounts for development (chat testing, etc.)'

    def handle(self, *args, **options):
        for data in TEST_STUDENTS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                },
            )

            if created:
                user.set_password(data['password'])
                user.save()
                Profile.objects.create(
                    user=user,
                    user_type='student',
                    email_verified=True,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Created: {data['first_name']} {data['last_name']} "
                    f"({data['email']}, id={user.id})"
                ))
            else:
                # Ensure profile exists and is verified
                profile, _ = Profile.objects.get_or_create(
                    user=user,
                    defaults={'user_type': 'student'},
                )
                if not profile.email_verified:
                    profile.email_verified = True
                    profile.save()
                self.stdout.write(
                    f"Already exists: {data['first_name']} {data['last_name']} "
                    f"({data['email']}, id={user.id})"
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Dev login URLs:'))
        for data in TEST_STUDENTS:
            user = User.objects.get(username=data['username'])
            self.stdout.write(
                f"  {data['first_name']} {data['last_name']}: "
                f"http://127.0.0.1:8000/chat/dev-login/{user.id}/"
            )
