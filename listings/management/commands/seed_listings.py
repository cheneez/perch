from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import ensure_account_profile, ensure_role_profile
from listings.models import Listing


class Command(BaseCommand):
    help = "Seed a sample realtor account and one listing for development."

    def handle(self, *args, **options):
        # Create (or fetch) the seed realtor user
        user, created = User.objects.get_or_create(
            username="realtor_seed",
            defaults={
                "email": "realtor@perch.dev",
                "first_name": "Seed",
                "last_name": "Realtor",
            },
        )
        if created:
            user.set_password("perch1234")
            user.save()
            self.stdout.write("  Created user: realtor_seed / perch1234")
        else:
            self.stdout.write("  User realtor_seed already exists — skipping creation")

        # Ensure the auth/profile graph matches what the app expects.
        profile = ensure_account_profile(
            user,
            user_type="realtor",
            email_verified=True,
        )
        ensure_role_profile(user, profile=profile)

        # Create one sample listing if none exist for this user
        if Listing.objects.filter(owner=user).exists():
            self.stdout.write("  Listing already exists for realtor_seed — skipping")
        else:
            Listing.objects.create(
                owner=user,
                title="Sunny 2BR Near Boston College",
                description=(
                    "Bright two-bedroom apartment just a short walk from campus. "
                    "Recently renovated kitchen, hardwood floors, and plenty of natural light. "
                    "Heat and hot water included."
                ),
                address="25 Commonwealth Ave, Brighton, MA 02135",
                price_monthly=2400,
                security_deposit=2400,
                bedrooms=2,
                bathrooms=1,
                distance_miles=0.4,
                room_type=Listing.RoomType.WHOLE_APARTMENT,
                lease_type=Listing.LeaseType.FULL,
                status=Listing.Status.AVAILABLE,
                moderation_status=Listing.ModerationStatus.APPROVED,
                utilities_included=True,
                has_laundry=True,
                has_ac_heat=True,
                parking_available=False,
                pets_allowed=False,
                latitude=42.3409,
                longitude=-71.1663,
            )
            self.stdout.write("  Created sample listing")

        self.stdout.write(self.style.SUCCESS("Done. Log in at /auth/login/ with realtor_seed / perch1234"))
