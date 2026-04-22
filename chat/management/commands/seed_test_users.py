from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from chat.models import Conversation, Message
from lessor.models import LessorProfile


TEST_STUDENTS = [
    {
        'username': 'teststudent1',
        'email': 'teststudent1@bc.edu',
        'first_name': 'Alice',
        'last_name': 'Chen',
        'password': 'testpass123',
        'verified': True,
    },
    {
        'username': 'teststudent2',
        'email': 'teststudent2@bc.edu',
        'first_name': 'Ben',
        'last_name': 'Torres',
        'password': 'testpass123',
        'verified': True,
    },
    {
        'username': 'teststudent3',
        'email': 'teststudent3@bc.edu',
        'first_name': 'Casey',
        'last_name': 'Park',
        'password': 'testpass123',
        'verified': False,  # unverified — won't appear in user_search
    },
]

TEST_LESSORS = [
    {
        'username': 'testlessor1',
        'email': 'testlessor1@realty.com',
        'first_name': 'Dana',
        'last_name': 'Mills',
        'password': 'testpass123',
        'verified': True,
    },
    {
        'username': 'testlessor2',
        'email': 'testlessor2@realty.com',
        'first_name': 'Evan',
        'last_name': 'Shaw',
        'password': 'testpass123',
        'verified': False,  # unverified — won't appear in lessor search
    },
]


class Command(BaseCommand):
    help = 'Seed test users (students + lessors) and sample conversations for chat dev'

    def handle(self, *args, **options):
        users = {}

        # ── Students ──────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('Students'))
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
            else:
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.save(update_fields=['first_name', 'last_name'])

            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={'user_type': 'student', 'email_verified': data['verified']},
            )
            if profile.email_verified != data['verified']:
                profile.email_verified = data['verified']
                profile.save(update_fields=['email_verified'])

            status = 'created' if created else 'exists'
            verified_label = 'verified' if data['verified'] else 'unverified'
            self.stdout.write(
                f"  [{status}] {data['first_name']} {data['last_name']} "
                f"({data['email']}, id={user.id}, {verified_label})"
            )
            users[data['username']] = user

        # ── Lessors ───────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('Lessors'))
        for data in TEST_LESSORS:
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
            else:
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.save(update_fields=['first_name', 'last_name'])

            Profile.objects.get_or_create(
                user=user,
                defaults={'user_type': 'realtor'},
            )

            lp, lp_created = LessorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'username': data['username'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'gender_identity': 'Prefer not to say',
                    'verified': data['verified'],
                },
            )
            if not lp_created and lp.verified != data['verified']:
                lp.verified = data['verified']
                lp.save(update_fields=['verified'])

            status = 'created' if created else 'exists'
            verified_label = 'verified' if data['verified'] else 'unverified'
            self.stdout.write(
                f"  [{status}] {data['first_name']} {data['last_name']} "
                f"({data['email']}, id={user.id}, {verified_label})"
            )
            users[data['username']] = user

        # ── Sample conversations ───────────────────────────────────
        s1 = users['teststudent1']
        s2 = users['teststudent2']
        s3 = users['teststudent3']
        l1 = users['testlessor1']

        self.stdout.write(self.style.MIGRATE_HEADING('Sample conversations'))

        # 1:1 student DM
        dm_student = self._get_or_create_dm(s1, s2)
        self._seed_messages(dm_student, [
            (s1, 'Hey Ben, are you looking for a roommate for next semester?'),
            (s2, 'Yeah! I saw your post on the group. What area are you thinking?'),
            (s1, 'Somewhere close to campus — Brighton or Allston ideally.'),
        ])
        self.stdout.write(f'  1:1 student DM  (id={dm_student.id}): Alice ↔ Ben')

        # 1:1 student–lessor DM
        dm_lessor = self._get_or_create_dm(s1, l1)
        self._seed_messages(dm_lessor, [
            (l1, 'Hi Alice, I saw you were interested in the Brighton listing.'),
            (s1, 'Yes! Is the unit still available for September?'),
            (l1, 'It is. Want to schedule a showing this weekend?'),
        ])
        self.stdout.write(f'  1:1 lessor DM   (id={dm_lessor.id}): Alice ↔ Dana (lessor)')

        # Student group chat (verified students only — s3 is unverified but still a valid participant)
        group_student = self._get_or_create_group(
            creator=s1,
            participants=[s2, s3],
            name='BC Housing Search',
        )
        self._seed_messages(group_student, [
            (s1, 'Welcome to the group! Let\'s coordinate our apartment search.'),
            (s2, 'Great idea. Anyone have listings to share?'),
            (s3, 'I found a 3BR on Commonwealth — sending the link now.'),
        ])
        self.stdout.write(f'  Student group   (id={group_student.id}): Alice, Ben, Casey')

        # Mixed group (students + lessor)
        group_mixed = self._get_or_create_group(
            creator=s1,
            participants=[s2, l1],
            name='Brighton Apartment Viewing',
        )
        self._seed_messages(group_mixed, [
            (l1, 'Hi everyone! The showing is Saturday at 11am.'),
            (s1, 'Perfect, we\'ll both be there.'),
            (s2, 'See you then, Dana!'),
        ])
        self.stdout.write(f'  Mixed group     (id={group_mixed.id}): Alice, Ben + Dana (lessor)')

        # ── Dev login URLs ────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Dev login URLs:'))
        for key, user in users.items():
            label = f'{user.first_name} {user.last_name}'
            self.stdout.write(f'  {label:20s}  http://127.0.0.1:8000/chat/dev-login/{user.id}/')

    # ── Helpers ───────────────────────────────────────────────────

    def _get_or_create_dm(self, user_a, user_b):
        existing = (
            Conversation.objects
            .filter(participants=user_a)
            .filter(participants=user_b)
            .filter(is_group=False)
            .first()
        )
        if existing:
            return existing
        conv = Conversation.objects.create(is_group=False, created_by=user_a)
        conv.participants.add(user_a, user_b)
        return conv

    def _get_or_create_group(self, creator, participants, name):
        existing = (
            Conversation.objects
            .filter(is_group=True, name=name)
            .filter(participants=creator)
            .first()
        )
        if existing:
            return existing
        conv = Conversation.objects.create(name=name, is_group=True, created_by=creator)
        conv.participants.add(creator, *participants)
        return conv

    def _seed_messages(self, conv, messages):
        if conv.messages.exists():
            return
        for sender, content in messages:
            Message.objects.create(conversation=conv, sender=sender, content=content)
        conv.save(update_fields=['updated_at'])
