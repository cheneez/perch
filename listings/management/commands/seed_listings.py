from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
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

        # Ensure profile is realtor + verified so the app lets them in
        profile, _ = Profile.objects.get_or_create(user=user, defaults={"user_type": "realtor"})
        if profile.user_type != "realtor" or not profile.email_verified:
            profile.user_type = "realtor"
            profile.email_verified = True
            profile.save()

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
                utilities_included=True,
                has_laundry=True,
                has_ac_heat=True,
                parking_available=False,
                pets_allowed=False,
            )
            self.stdout.write("  Created sample listing")

        self.stdout.write(self.style.SUCCESS("Done. Log in at /auth/login/ with realtor_seed / perch1234"))
