from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import ensure_account_profile, ensure_role_profile
from lessor.models import LessorProfile
from listings.models import Listing
from student.models import StudentCompatibilitySurvey, StudentProfile


TEST_PASSWORD = 'testpass123'
ADMIN_PASSWORD = 'perch1234'

STUDENT_SEEDS = [
    {
        'username': 'student_seed_1',
        'email': 'maya@bc.edu',
        'first_name': 'Maya',
        'last_name': 'Chen',
        'grade_year': 'ug_junior',
        'major': 'cs',
        'graduation_year': '2027',
        'display_name': 'Maya C.',
        'bio': 'Junior studying computer science. Usually at the gym, in O\'Neill, or trying new coffee spots off campus.',
        'hobbies': ['gym', 'music', 'traveling'],
        'employment_status': 'student_pt',
        'current_role': 'Library assistant',
        'housing_budget': '1200_1600',
        'can_contribute_rent': True,
        'phone_number': '617-555-0101',
        'instagram': 'maya.codes',
        'linkedin': 'https://linkedin.com/in/maya-chen-bc',
        'show_email': True,
        'show_instagram': True,
        'show_linkedin': True,
    },
    {
        'username': 'student_seed_2',
        'email': 'jackson@bc.edu',
        'first_name': 'Jackson',
        'last_name': 'Lee',
        'grade_year': 'ug_senior',
        'major': 'business',
        'graduation_year': '2026',
        'display_name': 'Jackson L.',
        'bio': 'Senior in Carroll with a structured schedule. Looking for a clean apartment and roommates who are friendly but independent.',
        'hobbies': ['sports', 'movies', 'reading'],
        'employment_status': 'internship',
        'current_role': 'Finance internship',
        'housing_budget': '1600_plus',
        'can_contribute_rent': True,
        'phone_number': '617-555-0102',
        'instagram': 'jacksonlee.bc',
        'linkedin': 'https://linkedin.com/in/jackson-lee-bc',
        'show_email': False,
        'show_instagram': True,
        'show_linkedin': True,
    },
    {
        'username': 'student_seed_3',
        'email': 'sofia@bc.edu',
        'first_name': 'Sofia',
        'last_name': 'Martinez',
        'grade_year': 'ug_sophomore',
        'major': 'psychology',
        'graduation_year': '2028',
        'display_name': 'Sofia M.',
        'bio': 'Sophomore psychology major who likes a social apartment but still needs quiet nights during exam weeks.',
        'hobbies': ['art', 'cooking', 'movies'],
        'employment_status': 'student',
        'current_role': 'Psychology club member',
        'housing_budget': '800_1200',
        'can_contribute_rent': True,
        'phone_number': '617-555-0103',
        'instagram': 'sofiastudies',
        'facebook': 'https://facebook.com/sofia.m.seed',
        'show_email': True,
        'show_instagram': True,
        'show_facebook': False,
    },
    {
        'username': 'student_seed_4',
        'email': 'declan@bc.edu',
        'first_name': 'Declan',
        'last_name': 'Murphy',
        'grade_year': 'ug_junior',
        'major': 'economics',
        'graduation_year': '2027',
        'display_name': 'Declan M.',
        'bio': 'Economics major who likes an active apartment and is usually out for runs, pickup basketball, or grabbing dinner with friends.',
        'hobbies': ['sports', 'hiking', 'gaming'],
        'employment_status': 'part_time',
        'current_role': 'Campus rec staff',
        'housing_budget': '1200_1600',
        'can_contribute_rent': True,
        'phone_number': '617-555-0104',
        'instagram': 'declan.moves',
        'handshake': 'https://app.joinhandshake.com/stu/users/declan-seed',
        'show_phone': True,
        'show_instagram': True,
        'show_handshake': False,
    },
    {
        'username': 'student_seed_5',
        'email': 'nina@bc.edu',
        'first_name': 'Nina',
        'last_name': 'Patel',
        'grade_year': 'grad_1',
        'major': 'biology',
        'graduation_year': '2026',
        'display_name': 'Nina P.',
        'bio': 'Graduate biology student with a quieter routine. Looking for roommates who value cleanliness and a calm shared space.',
        'hobbies': ['reading', 'hiking', 'music'],
        'employment_status': 'full_time',
        'current_role': 'Research lab assistant',
        'housing_budget': '1600_plus',
        'can_contribute_rent': True,
        'phone_number': '617-555-0105',
        'linkedin': 'https://linkedin.com/in/nina-patel-bc',
        'facebook': 'https://facebook.com/nina.p.seed',
        'show_email': True,
        'show_linkedin': True,
        'show_facebook': False,
    },
]

LESSOR_SEEDS = [
    {
        'username': 'lessor_seed_1',
        'email': 'casey.agent@example.com',
        'first_name': 'Casey',
        'last_name': 'Agent',
        'display_name': 'Casey Agent',
        'bio': 'Leasing manager covering Brighton and Allston with a focus on student-friendly apartments near BC.',
        'phone_number': '617-555-0201',
        'instagram': 'caseyshowsapartments',
        'linkedin': 'https://linkedin.com/in/casey-agent',
        'verified': True,
    },
    {
        'username': 'lessor_seed_2',
        'email': 'riley.realty@example.com',
        'first_name': 'Riley',
        'last_name': 'Brooks',
        'display_name': 'Riley Brooks',
        'bio': 'Independent realtor working with graduate students and groups looking for clean, well-managed multi-bedroom units.',
        'phone_number': '617-555-0202',
        'instagram': 'rileyrealty',
        'linkedin': 'https://linkedin.com/in/riley-brooks-realty',
        'verified': True,
    },
    {
        'username': 'lessor_seed_3',
        'email': 'jordan.homes@example.com',
        'first_name': 'Jordan',
        'last_name': 'Diaz',
        'display_name': 'Jordan Diaz',
        'bio': 'Small landlord portfolio owner focused on renovated units with transparent pricing and responsive communication.',
        'phone_number': '617-555-0203',
        'instagram': 'jordanhomesboston',
        'linkedin': 'https://linkedin.com/in/jordan-diaz-homes',
        'verified': True,
    },
]

LISTING_SEEDS = [
    {
        'owner_username': 'lessor_seed_1',
        'title': 'Sunny 2BR Near Boston College',
        'address': '25 Commonwealth Ave, Brighton, MA 02135',
        'price_monthly': 2400,
        'bedrooms': 2,
        'bathrooms': 1,
        'distance_miles': 0.4,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.FULL,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.APPROVED,
        'latitude': 42.3409,
        'longitude': -71.1663,
        'description': 'Bright two-bedroom apartment with hardwood floors, updated kitchen finishes, and an easy walk to the BC shuttle. Good fit for two students who want a classic Brighton layout close to campus.',
        'security_deposit': 2400,
        'broker_fee': 1200,
        'application_fee': 35,
        'estimated_utilities_cost': 120,
        'lease_start': date(2026, 9, 1),
        'lease_end': date(2027, 8, 31),
        'utilities_included': True,
        'has_laundry': True,
        'has_ac_heat': True,
        'parking_available': False,
        'pets_allowed': False,
        'shared_space': False,
    },
    {
        'owner_username': 'lessor_seed_1',
        'title': 'Garden Level Studio on Foster St',
        'address': '91 Foster St, Brighton, MA 02135',
        'price_monthly': 1750,
        'bedrooms': 1,
        'bathrooms': 1,
        'distance_miles': 0.8,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.SUBLEASE,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.PENDING,
        'latitude': 42.3447,
        'longitude': -71.1578,
        'description': 'Compact studio with a separate kitchen nook and easy access to Brighton Center buses. Pending moderation because the listing copy and image set still need review.',
        'security_deposit': 1750,
        'broker_fee': 875,
        'application_fee': 25,
        'estimated_utilities_cost': 90,
        'lease_start': date(2026, 7, 1),
        'lease_end': date(2027, 5, 31),
        'utilities_included': False,
        'has_laundry': False,
        'has_ac_heat': True,
        'parking_available': False,
        'pets_allowed': False,
        'shared_space': False,
    },
    {
        'owner_username': 'lessor_seed_2',
        'title': '3BR Split with Laundry and Parking',
        'address': '19 Undine Rd, Brighton, MA 02135',
        'price_monthly': 3450,
        'bedrooms': 3,
        'bathrooms': 1,
        'distance_miles': 0.7,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.FULL,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.APPROVED,
        'latitude': 42.3428,
        'longitude': -71.1619,
        'description': 'Well-laid-out three-bedroom split with laundry in the basement, one driveway parking spot, and strong value for a student group trying to stay close to Cleveland Circle.',
        'security_deposit': 3450,
        'broker_fee': 1725,
        'application_fee': 40,
        'estimated_utilities_cost': 180,
        'lease_start': date(2026, 9, 1),
        'lease_end': date(2027, 8, 31),
        'utilities_included': False,
        'has_laundry': True,
        'has_ac_heat': True,
        'parking_available': True,
        'pets_allowed': True,
        'shared_space': False,
    },
    {
        'owner_username': 'lessor_seed_2',
        'title': 'Private Room in Oak Square House',
        'address': '34 Tremont St, Brighton, MA 02135',
        'price_monthly': 1100,
        'bedrooms': 1,
        'bathrooms': 1,
        'distance_miles': 1.5,
        'room_type': Listing.RoomType.ROOM,
        'lease_type': Listing.LeaseType.SUBLEASE,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.APPROVED,
        'latitude': 42.3502,
        'longitude': -71.1534,
        'description': 'One private bedroom available in a shared single-family house. Best for a student who wants a lower monthly rent and does not mind living with other roommates.',
        'security_deposit': 1100,
        'broker_fee': 0,
        'application_fee': 20,
        'estimated_utilities_cost': 75,
        'lease_start': date(2026, 6, 15),
        'lease_end': date(2027, 5, 31),
        'utilities_included': False,
        'has_laundry': True,
        'has_ac_heat': False,
        'parking_available': False,
        'pets_allowed': False,
        'shared_space': True,
    },
    {
        'owner_username': 'lessor_seed_3',
        'title': 'Renovated 4BR Near Green Line',
        'address': '12 Sutherland Rd, Brighton, MA 02135',
        'price_monthly': 4200,
        'bedrooms': 4,
        'bathrooms': 2,
        'distance_miles': 1.1,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.FULL,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.APPROVED,
        'latitude': 42.3438,
        'longitude': -71.1442,
        'description': 'Large four-bedroom apartment with two full baths, refreshed kitchen, and quick access to the Green Line. Good option for a larger group splitting costs.',
        'security_deposit': 4200,
        'broker_fee': 2100,
        'application_fee': 45,
        'estimated_utilities_cost': 220,
        'lease_start': date(2026, 9, 1),
        'lease_end': date(2027, 8, 31),
        'utilities_included': False,
        'has_laundry': True,
        'has_ac_heat': True,
        'parking_available': True,
        'pets_allowed': True,
        'shared_space': False,
    },
    {
        'owner_username': 'lessor_seed_3',
        'title': 'One Bedroom Lease Takeover',
        'address': '48 Strathmore Rd, Brighton, MA 02135',
        'price_monthly': 1895,
        'bedrooms': 1,
        'bathrooms': 1,
        'distance_miles': 1.0,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.SUBLEASE,
        'status': Listing.Status.RENTED,
        'moderation_status': Listing.ModerationStatus.APPROVED,
        'latitude': 42.3424,
        'longitude': -71.1496,
        'description': 'Single-bedroom lease takeover that has already been filled. Useful for testing rented-state behavior in listings and admin dashboards.',
        'security_deposit': 1895,
        'broker_fee': 0,
        'application_fee': 0,
        'estimated_utilities_cost': 95,
        'lease_start': date(2026, 5, 1),
        'lease_end': date(2026, 8, 31),
        'utilities_included': False,
        'has_laundry': True,
        'has_ac_heat': True,
        'parking_available': False,
        'pets_allowed': False,
        'shared_space': False,
    },
    {
        'owner_username': 'lessor_seed_2',
        'title': 'Top Floor 2BR with New Kitchen',
        'address': '72 Chiswick Rd, Brighton, MA 02135',
        'price_monthly': 2700,
        'bedrooms': 2,
        'bathrooms': 1,
        'distance_miles': 1.2,
        'room_type': Listing.RoomType.WHOLE_APARTMENT,
        'lease_type': Listing.LeaseType.FULL,
        'status': Listing.Status.AVAILABLE,
        'moderation_status': Listing.ModerationStatus.REJECTED,
        'latitude': 42.3396,
        'longitude': -71.1517,
        'description': 'Two-bedroom unit with a renovated kitchen and good natural light. Seeded as rejected so moderation views have a realistic declined example.',
        'security_deposit': 2700,
        'broker_fee': 1350,
        'application_fee': 35,
        'estimated_utilities_cost': 130,
        'lease_start': date(2026, 9, 1),
        'lease_end': date(2027, 8, 31),
        'utilities_included': False,
        'has_laundry': False,
        'has_ac_heat': True,
        'parking_available': False,
        'pets_allowed': True,
        'shared_space': False,
    },
]


class Command(BaseCommand):
    help = 'Populate local dev with test students, lessors, surveys, listings, and one admin account.'

    def handle(self, *args, **options):
        self._seed_admin_user()
        self._seed_students()
        self._seed_lessors()
        self._seed_listings()
        self.stdout.write(self.style.SUCCESS('Done. Local test data is ready.'))

    def _seed_admin_user(self):
        user, created = User.objects.get_or_create(
            username='admin_seed',
            defaults={
                'email': 'admin@perch.dev',
                'first_name': 'Perch',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            user.set_password(ADMIN_PASSWORD)
            user.save()
        else:
            changed = []
            if not user.is_staff:
                user.is_staff = True
                changed.append('is_staff')
            if not user.is_superuser:
                user.is_superuser = True
                changed.append('is_superuser')
            if changed:
                user.save(update_fields=changed)

        ensure_account_profile(user, user_type='admin', email_verified=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin ready: admin_seed / {ADMIN_PASSWORD}"
            )
        )

    def _seed_students(self):
        for idx, row in enumerate(STUDENT_SEEDS, start=1):
            user, created = User.objects.get_or_create(
                username=row['username'],
                defaults={
                    'email': row['email'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                },
            )
            if created:
                user.set_password(TEST_PASSWORD)
                user.save()

            profile = ensure_account_profile(
                user,
                user_type='student',
                email_verified=True,
            )
            student_profile = ensure_role_profile(user, profile=profile)
            StudentProfile.objects.filter(pk=student_profile.pk).update(
                school='Boston College',
                grade_year=row['grade_year'],
                gender_identity='prefer_not',
                email=row['email'],
                display_name=row['display_name'],
                bio=row['bio'],
                hobbies=row['hobbies'],
                employment_status=row['employment_status'],
                current_role=row['current_role'],
                housing_budget=row['housing_budget'],
                can_contribute_rent=row['can_contribute_rent'],
                phone_number=row['phone_number'],
                instagram=row.get('instagram', ''),
                linkedin=row.get('linkedin', ''),
                handshake=row.get('handshake', ''),
                facebook=row.get('facebook', ''),
                show_email=row.get('show_email', False),
                show_phone=row.get('show_phone', False),
                show_instagram=row.get('show_instagram', True),
                show_linkedin=row.get('show_linkedin', True),
                show_handshake=row.get('show_handshake', False),
                show_facebook=row.get('show_facebook', False),
            )
            StudentCompatibilitySurvey.objects.update_or_create(
                user=user,
                defaults={
                    'graduation_year': row['graduation_year'],
                    'major': row['major'],
                    'pets': 's3_depends',
                    'smoking_habits': 's1_no_smoking' if idx % 2 else 's2_outside_only',
                    'party_at_home': 's2_rarely' if idx % 2 else 's3_sometimes',
                    'sleep_schedule': 's4_somewhat_early' if idx % 2 else 's2_somewhat_late',
                    'roommate_relationship': 's3_balanced',
                    'morning_night_preference': 's5_morning_with_morning' if idx % 2 else 's2_night_can_live_morning',
                    'personality': 's3_in_between',
                    'cleanliness': 's4_neat',
                    'guests': 's2_sometimes',
                    'noise_level': 's2_quiet' if idx % 2 else 's3_moderate',
                    'study_at_home': 's4_often',
                    'conflict_style': 's3_calm',
                },
            )
            self.stdout.write(f"Student ready: {row['username']} / {TEST_PASSWORD}")

    def _seed_lessors(self):
        for row in LESSOR_SEEDS:
            user, created = User.objects.get_or_create(
                username=row['username'],
                defaults={
                    'email': row['email'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                },
            )
            if created:
                user.set_password(TEST_PASSWORD)
                user.save()

            profile = ensure_account_profile(
                user,
                user_type='realtor',
                email_verified=True,
            )
            lessor_profile = ensure_role_profile(user, profile=profile)
            LessorProfile.objects.filter(pk=lessor_profile.pk).update(
                email=row['email'],
                date_of_birth=date(1995, 1, 1),
                gender_identity='prefer_not',
                display_name=row['display_name'],
                bio=row['bio'],
                phone_number=row['phone_number'],
                instagram=row['instagram'],
                linkedin=row['linkedin'],
                verified=row['verified'],
                show_email=True,
                show_phone=True,
                show_instagram=True,
                show_linkedin=True,
            )
            self.stdout.write(f"Lessor ready: {row['username']} / {TEST_PASSWORD}")

    def _seed_listings(self):
        for seed in LISTING_SEEDS:
            owner = User.objects.get(username=seed['owner_username'])
            defaults = {
                'description': seed['description'],
                'address': seed['address'],
                'price_monthly': seed['price_monthly'],
                'security_deposit': seed['security_deposit'],
                'broker_fee': seed['broker_fee'],
                'application_fee': seed['application_fee'],
                'estimated_utilities_cost': seed['estimated_utilities_cost'],
                'bedrooms': seed['bedrooms'],
                'bathrooms': seed['bathrooms'],
                'distance_miles': seed['distance_miles'],
                'room_type': seed['room_type'],
                'lease_type': seed['lease_type'],
                'lease_start': seed['lease_start'],
                'lease_end': seed['lease_end'],
                'status': seed['status'],
                'moderation_status': seed['moderation_status'],
                'utilities_included': seed['utilities_included'],
                'has_laundry': seed['has_laundry'],
                'has_ac_heat': seed['has_ac_heat'],
                'parking_available': seed['parking_available'],
                'pets_allowed': seed['pets_allowed'],
                'shared_space': seed['shared_space'],
                'latitude': seed['latitude'],
                'longitude': seed['longitude'],
            }
            listing, created = Listing.objects.update_or_create(
                owner=owner,
                title=seed['title'],
                defaults=defaults,
            )
            created_label = 'Created' if created else 'Updated'
            self.stdout.write(f"{created_label} listing: {listing.title}")
