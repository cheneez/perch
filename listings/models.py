from django.conf import settings
from django.db import models


class ListingQuerySet(models.QuerySet):
    def publicly_visible(self):
        return self.filter(moderation_status='approved')

    def accessible_to(self, user):
        visible = self.publicly_visible()
        if user and user.is_authenticated:
            return self.filter(
                models.Q(moderation_status='approved') | models.Q(owner=user)
            ).distinct()
        return visible


class Listing(models.Model):
    class RoomType(models.TextChoices):
        ROOM = "room", "Room"
        WHOLE_APARTMENT = "whole_apartment", "Whole Apartment"
    class LeaseType(models.TextChoices):
        FULL = "full", "Full Lease"
        SUBLEASE = "sublease", "Sublease"
        SHORT_TERM = "short_term", "Short Term"
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        PENDING = "pending", "Pending"
        RENTED = "rented", "Rented"
    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    objects = ListingQuerySet.as_manager()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    utilities_included = models.BooleanField(default=False)
    estimated_utilities_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    security_deposit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    broker_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    application_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_upfront_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    distance_miles = models.FloatField(default=0.0)
    has_laundry = models.BooleanField(default=False)
    has_ac_heat = models.BooleanField(default=False)
    avg_rating = models.FloatField(default=0.0)
    image_count = models.IntegerField(default=0)
    video_count = models.IntegerField(default=0)
    parking_available = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    stairs = models.BooleanField(default=False)
    shared_space = models.BooleanField(default=False)
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
    )
    lease_type = models.CharField(
        max_length=20,
        choices=LeaseType.choices,
    )
    lease_start = models.DateField(null=True, blank=True)
    lease_end = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='moderated_listings',
    )
    moderation_notes = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.verified = self.moderation_status == self.ModerationStatus.APPROVED
        super().save(*args, **kwargs)


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="images",
    )
    # Existing rows may already be in the DB. Make uploads optional so
    # migrations can apply without forcing a default file.
    image = models.ImageField(upload_to="listing_images/", null=True, blank=True)
    # Keep legacy column (from earlier URL-based implementation) optional.
    image_url = models.URLField(max_length=500, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Image for listing {self.listing_id}"
# Create your models here.
