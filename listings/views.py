import json
import urllib.parse
import urllib.request

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from chat.models import Conversation, Message
from .forms import ListingForm
from .models import Listing, ListingFavorite, ListingImage, ListingReview


def _geocode(address):
    """Return (lat, lng) for address using Nominatim, or (None, None) on failure."""
    url = (
        "https://nominatim.openstreetmap.org/search?q="
        + urllib.parse.quote(address)
        + "&format=json&limit=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "perch-housing-app/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            results = json.loads(resp.read())
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()

            lat, lng = _geocode(listing.address)
            if lat is not None:
                Listing.objects.filter(pk=listing.pk).update(latitude=lat, longitude=lng)

            images = request.FILES.getlist("images")
            for image in images:
                ListingImage.objects.create(listing=listing, image=image)

            messages.success(request, "Listing created successfully.")
            return redirect("listings:listing-detail", pk=listing.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = ListingForm()
    return render(request, "listings/create_fixed.html", {"form": form})


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
                lat, lng = _geocode(listing.address)
                if lat is not None:
                    Listing.objects.filter(pk=listing.pk).update(latitude=lat, longitude=lng)

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
    return render(request, "listings/edit.html", {"form": form, "listing": listing})


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
    is_favorited = False
    user_review = None
    if request.user.is_authenticated:
        is_favorited = ListingFavorite.objects.filter(user=request.user, listing=listing).exists()
        user_review = ListingReview.objects.filter(user=request.user, listing=listing).first()
    return render(
        request,
        'listings/property.html',
        {
            'listing': listing,
            'is_favorited': is_favorited,
            'user_review': user_review,
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
