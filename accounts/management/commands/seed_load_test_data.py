import json
import random
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import ensure_account_profile, ensure_role_profile
from chat.models import Conversation, Message
from lessor.models import LessorProfile
from listings.models import Listing
from student.models import StudentCompatibilitySurvey


class Command(BaseCommand):
    help = "Generate medium-scale load test data and credential manifest."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=500)
        parser.add_argument("--lessors", type=int, default=120)
        parser.add_argument("--listings-per-lessor", type=int, default=8)
        parser.add_argument("--conversations", type=int, default=700)
        parser.add_argument("--messages-per-conversation", type=int, default=12)
        parser.add_argument("--password", type=str, default="testpass123")
        parser.add_argument(
            "--output",
            type=str,
            default="performance/locust/data/credentials.json",
        )

    def handle(self, *args, **options):
        random.seed(42)
        password = options["password"]
        students = self._ensure_students(options["students"], password)
        lessors = self._ensure_lessors(options["lessors"], password)
        self._ensure_listings(lessors, options["listings_per_lessor"])
        self._ensure_conversations(
            students,
            lessors,
            options["conversations"],
            options["messages_per_conversation"],
        )
        self._write_manifest(
            students=students,
            lessors=lessors,
            password=password,
            output_path=options["output"],
            options=options,
        )
        self.stdout.write(self.style.SUCCESS("Load test data seeding complete."))

    def _ensure_students(self, total, password):
        created = []
        for index in range(1, total + 1):
            username = f"lt_student_{index:04d}"
            email = f"{username}@bc.edu"
            first_name = f"Student{index}"
            last_name = "Load"
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if was_created:
                user.set_password(password)
                user.save()
            ensure_account_profile(user, user_type="student", email_verified=True)
            ensure_role_profile(user)
            StudentCompatibilitySurvey.objects.update_or_create(
                user=user,
                defaults={
                    "graduation_year": random.choice(["2026", "2027", "2028", "2029"]),
                    "major": random.choice(["cs", "business", "economics", "biology", "psychology"]),
                    "pets": "s3_depends",
                    "smoking_habits": "s1_no_smoking",
                    "party_at_home": random.choice(["s2_rarely", "s3_sometimes"]),
                    "sleep_schedule": random.choice(["s2_somewhat_late", "s4_somewhat_early"]),
                    "roommate_relationship": "s3_balanced",
                    "morning_night_preference": random.choice(["s5_morning_with_morning", "s2_night_can_live_morning"]),
                    "personality": random.choice(["s2_fairly_shy", "s3_in_between", "s4_fairly_outgoing"]),
                    "cleanliness": random.choice(["s3_average", "s4_neat"]),
                    "guests": random.choice(["s2_sometimes", "s3_weekends"]),
                    "noise_level": random.choice(["s2_quiet", "s3_moderate"]),
                    "study_at_home": random.choice(["s3_sometimes", "s4_often"]),
                    "conflict_style": "s3_calm",
                },
            )
            created.append({"username": username, "email": email, "password": password})
        return created

    def _ensure_lessors(self, total, password):
        created = []
        for index in range(1, total + 1):
            username = f"lt_lessor_{index:04d}"
            email = f"{username}@realty.example.com"
            first_name = f"Lessor{index}"
            last_name = "Load"
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if was_created:
                user.set_password(password)
                user.save()
            ensure_account_profile(user, user_type="realtor", email_verified=True)
            ensure_role_profile(user)
            LessorProfile.objects.filter(user=user).update(
                verified=True,
                show_email=True,
                show_phone=True,
                show_instagram=False,
                show_linkedin=False,
            )
            created.append({"username": username, "email": email, "password": password})
        return created

    def _ensure_listings(self, lessors, listings_per_lessor):
        for lessor_row in lessors:
            owner = User.objects.get(username=lessor_row["username"])
            for listing_index in range(1, listings_per_lessor + 1):
                title = f"Load Listing {owner.username}-{listing_index}"
                start_date = date(2026, 9, 1)
                Listing.objects.update_or_create(
                    owner=owner,
                    title=title,
                    defaults={
                        "description": "Generated for load testing.",
                        "address": f"{100 + listing_index} Test St, Brighton, MA",
                        "price_monthly": 1800 + (listing_index * 75),
                        "security_deposit": 1000,
                        "broker_fee": 500,
                        "application_fee": 25,
                        "estimated_utilities_cost": 120,
                        "bedrooms": random.choice([1, 2, 3, 4]),
                        "bathrooms": random.choice([1, 2]),
                        "distance_miles": round(random.uniform(0.3, 2.0), 2),
                        "room_type": random.choice([Listing.RoomType.ROOM, Listing.RoomType.WHOLE_APARTMENT]),
                        "lease_type": random.choice([Listing.LeaseType.FULL, Listing.LeaseType.SUBLEASE]),
                        "lease_start": start_date,
                        "lease_end": start_date + timedelta(days=365),
                        "status": Listing.Status.AVAILABLE,
                        "moderation_status": Listing.ModerationStatus.APPROVED,
                        "utilities_included": random.choice([True, False]),
                        "has_laundry": random.choice([True, False]),
                        "has_ac_heat": random.choice([True, False]),
                        "parking_available": random.choice([True, False]),
                        "pets_allowed": random.choice([True, False]),
                        "shared_space": random.choice([True, False]),
                        "latitude": 42.33 + random.random() / 100,
                        "longitude": -71.16 - random.random() / 100,
                    },
                )

    def _ensure_conversations(self, students, lessors, total_conversations, messages_per_conversation):
        student_users = [User.objects.get(username=row["username"]) for row in students]
        lessor_users = [User.objects.get(username=row["username"]) for row in lessors]
        if not student_users:
            return

        for idx in range(total_conversations):
            if idx % 3 == 0 and len(student_users) >= 2:
                user_a, user_b = random.sample(student_users, 2)
                conversation = (
                    Conversation.objects.filter(participants=user_a)
                    .filter(participants=user_b)
                    .filter(is_group=False)
                    .first()
                )
                if conversation is None:
                    conversation = Conversation.objects.create(is_group=False, created_by=user_a)
                    conversation.participants.add(user_a, user_b)
                participants = [user_a, user_b]
            else:
                group_size = random.choice([3, 4, 5])
                pool = student_users + lessor_users
                participants = random.sample(pool, min(group_size, len(pool)))
                leader = participants[0]
                conversation = Conversation.objects.create(
                    name=f"Load Group {idx + 1}",
                    is_group=True,
                    created_by=leader,
                )
                conversation.participants.add(*participants)

            if conversation.messages.exists():
                continue
            for msg_idx in range(messages_per_conversation):
                sender = participants[msg_idx % len(participants)]
                Message.objects.create(
                    conversation=conversation,
                    sender=sender,
                    content=f"Load message {msg_idx + 1} in conversation {conversation.id}",
                )
            conversation.save(update_fields=["updated_at"])

    def _write_manifest(self, students, lessors, password, output_path, options):
        manifest = {
            "metadata": {
                "students": options["students"],
                "lessors": options["lessors"],
                "listings_per_lessor": options["listings_per_lessor"],
                "conversations": options["conversations"],
                "messages_per_conversation": options["messages_per_conversation"],
                "default_password": password,
            },
            "students": students,
            "lessors": lessors,
        }
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(manifest, indent=2))
        self.stdout.write(f"Wrote credential manifest: {output_file}")

