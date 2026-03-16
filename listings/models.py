from django.conf import settings
from django.db import models


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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
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
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Image for {self.listing_id}"
# Create your models here.
