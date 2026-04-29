import json
import math
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from chat.models import Conversation, Message
from .forms import ListingForm, StudentSubleaseForm
from .models import Listing, ListingFavorite, ListingImage, ListingReview

BC_MAIN_CAMPUS_LAT = 42.3355
BC_MAIN_CAMPUS_LNG = -71.1685


def _lat_lng_from_post(post):
    """Extract lat/lng submitted by Places Autocomplete, or return (None, None)."""
    try:
        return float(post.get('_lat', '')), float(post.get('_lng', ''))
    except (ValueError, TypeError):
        return None, None


def _google_geocode(address):
    """Return (lat, lng) for address using Google Geocoding, or (None, None)."""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key or not address:
        return None, None

    query = urllib.parse.urlencode({
        "address": address,
        "key": api_key,
    })
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "perch-housing-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            results = json.loads(resp.read())
            if results.get("status") != "OK":
                return None, None

            top_result = results.get("results", [{}])[0]
            location = top_result.get("geometry", {}).get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            if lat is None or lng is None:
                return None, None
            return float(lat), float(lng)
    except Exception:
        pass
    return None, None


def _distance_miles_from_bc(lat, lng):
    """Return straight-line miles from BC main campus to a lat/lng pair."""
    earth_radius_miles = 3958.8
    d_lat = math.radians(lat - BC_MAIN_CAMPUS_LAT)
    d_lng = math.radians(lng - BC_MAIN_CAMPUS_LNG)
    origin_lat = math.radians(BC_MAIN_CAMPUS_LAT)
    dest_lat = math.radians(lat)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(origin_lat) * math.cos(dest_lat) * math.sin(d_lng / 2) ** 2
    )
    return earth_radius_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _update_listing_location_data(listing, post):
    lat, lng = _lat_lng_from_post(post)
    if lat is None:
        lat, lng = _google_geocode(listing.address)
    if lat is not None and lng is not None:
        distance_miles = round(_distance_miles_from_bc(lat, lng), 2)
        Listing.objects.filter(pk=listing.pk).update(
            latitude=lat,
            longitude=lng,
            distance_miles=distance_miles,
        )
        listing.latitude = lat
        listing.longitude = lng
        listing.distance_miles = distance_miles

def _is_student(user):
    try:
        return user.profile.user_type == "student"
    except Exception:
        return False


def _listing_form_class(user):
    return StudentSubleaseForm if _is_student(user) else ListingForm


@login_required
def create_listing(request):
    is_student_sublease = _is_student(request.user)
    FormClass = _listing_form_class(request.user)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        images = request.FILES.getlist("images")
        photo_required_error = ""

        if not images:
            photo_required_error = "This field is required."

        if form.is_valid():
            if photo_required_error:
                form.add_error(None, "Please upload at least one photo.")
                return render(request, "listings/create_fixed.html", {
                    "form": form,
                    "is_student_sublease": is_student_sublease,
                    "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
                    "photo_required_error": photo_required_error,
                })

            listing = form.save(commit=False)
            listing.owner = request.user
            if is_student_sublease:
                listing.lease_type = "sublease"
            listing.save()
            _update_listing_location_data(listing, request.POST)

            for image in images:
                ListingImage.objects.create(listing=listing, image=image)

            messages.success(request, "Listing created and submitted for approval.")
            return redirect("listings:listing-detail", pk=listing.pk)

        return render(request, "listings/create_fixed.html", {
            "form": form,
            "is_student_sublease": is_student_sublease,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "photo_required_error": photo_required_error,
        })
    else:
        form = FormClass()
    return render(request, "listings/create_fixed.html", {
        "form": form,
        "is_student_sublease": is_student_sublease,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def listings_list(request):
    listings = Listing.objects.filter(owner=request.user).prefetch_related("images").order_by("-created_at")
    return render(request, "listings/list.html", {"listings": listings})


@login_required
def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    return render(request, "listings/detail.html", {"listing": listing})


@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    is_student_sublease = _is_student(request.user)
    FormClass = _listing_form_class(request.user)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            updated = form.save(commit=False)
            if is_student_sublease:
                updated.lease_type = "sublease"
            updated.save()

            if updated.latitude is None or "address" in form.changed_data:
                _update_listing_location_data(updated, request.POST)

            delete_ids = request.POST.getlist("delete_images")
            if delete_ids:
                ListingImage.objects.filter(listing=updated, id__in=delete_ids).delete()

            images = request.FILES.getlist("images")
            for image in images:
                ListingImage.objects.create(listing=updated, image=image)

            messages.success(request, "Listing updated successfully.")
            return redirect("listings:listing-detail", pk=updated.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = FormClass(instance=listing)
    return render(request, "listings/edit.html", {
        "form": form,
        "listing": listing,
        "is_student_sublease": is_student_sublease,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)

    if request.method == "POST":
        listing.delete()
        messages.success(request, "Listing deleted successfully.")
        return redirect("listings:listings-list")

    # Basic fallback: redirect back if someone visits GET.
    return redirect("listings:listing-detail", pk=pk)


@login_required
@require_POST
def toggle_listing_visibility(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    listing.is_hidden = not listing.is_hidden
    listing.save(update_fields=["is_hidden"])
    messages.success(
        request,
        "Listing hidden." if listing.is_hidden else "Listing is visible again.",
    )
    return redirect("listings:listings-list")


def property_detail(request, pk):
    from groups.models import Group

    listing = get_object_or_404(Listing.objects.accessible_to(request.user), pk=pk)
    is_favorited = False
    user_review = None
    user_member_groups = []
    default_back_url = reverse("student:find_housing")
    back_to_listings_url = default_back_url
    requested_back_url = (request.GET.get("back") or "").strip()
    if requested_back_url and url_has_allowed_host_and_scheme(
        url=requested_back_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        back_to_listings_url = requested_back_url

    referer = request.META.get("HTTP_REFERER", "").strip()
    if (
        back_to_listings_url == default_back_url
        and referer
        and "/groups/save-listing/" not in referer
        and "/groups/remove-listing/" not in referer
        and request.path not in referer
        and url_has_allowed_host_and_scheme(
            url=referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        back_to_listings_url = referer
    if request.user.is_authenticated:
        is_favorited = ListingFavorite.objects.filter(user=request.user, listing=listing).exists()
        user_review = ListingReview.objects.filter(user=request.user, listing=listing).first()
        user_member_groups = list(
            Group.objects.filter(memberships__user=request.user)
            .order_by("name")
            .distinct()
        )
    return render(
        request,
        'listings/property.html',
        {
            'listing': listing,
            'is_favorited': is_favorited,
            'user_review': user_review,
            'back_to_listings_url': back_to_listings_url,
            'user_member_groups': user_member_groups,
        },
    )


@login_required
@require_POST
def contact_realtor(request, pk):
    listing = get_object_or_404(Listing.objects.accessible_to(request.user), pk=pk)
    body = request.POST.get("message", "").strip()

    if not body:
        messages.error(request, "Please enter a message before contacting the realtor.")
        return redirect("listings:property", pk=listing.pk)

    if request.user == listing.owner:
        messages.error(request, "You cannot message yourself about your own listing.")
        return redirect("listings:property", pk=listing.pk)

    conversation = (
        Conversation.objects
        .filter(participants=request.user)
        .filter(participants=listing.owner)
        .first()
    )
    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, listing.owner)

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=body,
    )
    # Touch the conversation so inbox ordering shows latest activity.
    conversation.save(update_fields=["updated_at"])

    messages.success(request, "Message sent to the realtor.")
    return redirect("student:find_housing")


@login_required
@require_POST
def submit_review(request, pk):
    listing = get_object_or_404(Listing.objects.accessible_to(request.user), pk=pk)
    if request.user == listing.owner:
        messages.error(request, "You cannot review your own listing.")
        return redirect("listings:property", pk=listing.pk)

    try:
        stars = int(request.POST.get("stars", "0"))
    except ValueError:
        stars = 0

    if stars < 1 or stars > 5:
        messages.error(request, "Please choose a star rating between 1 and 5.")
        return redirect("listings:property", pk=listing.pk)

    ListingReview.objects.update_or_create(
        user=request.user,
        listing=listing,
        defaults={"stars": stars},
    )

    avg = listing.reviews.aggregate(avg=Avg("stars"))["avg"] or 0.0
    listing.avg_rating = round(float(avg), 2)
    listing.save(update_fields=["avg_rating"])

    messages.success(request, "Thanks! Your review was submitted.")
    return redirect("listings:property", pk=listing.pk)
