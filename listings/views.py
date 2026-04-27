import json
import math
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ListingForm
from .models import Listing, ListingImage

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

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            _update_listing_location_data(listing, request.POST)

            images = request.FILES.getlist("images")
            for image in images:
                ListingImage.objects.create(listing=listing, image=image)

            messages.success(request, "Listing created successfully.")
            return redirect("listings:listing-detail", pk=listing.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = ListingForm()
    return render(request, "listings/create_fixed.html", {
        "form": form,
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
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            listing = form.save()

            if listing.latitude is None or "address" in form.changed_data:
                _update_listing_location_data(listing, request.POST)

            delete_ids = request.POST.getlist("delete_images")
            if delete_ids:
                ListingImage.objects.filter(listing=listing, id__in=delete_ids).delete()

            images = request.FILES.getlist("images")
            for image in images:
                ListingImage.objects.create(listing=listing, image=image)

            messages.success(request, "Listing updated successfully.")
            return redirect("listings:listing-detail", pk=listing.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = ListingForm(instance=listing)
    return render(request, "listings/edit.html", {
        "form": form,
        "listing": listing,
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

def property_detail(request, pk):
    listing = get_object_or_404(Listing.objects.accessible_to(request.user), pk=pk)
    return render(request, 'listings/property.html', {'listing': listing})
