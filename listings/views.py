from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Listing

# Create your views here.
def create_listing(request):
    return render(request, "listings/create.html")

def listings_list(request):
    return render(request, "listings/list.html")
    
def listing_detail(request):
    return render(request, "listings/detail.html")

@login_required
def property_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, 'listings/property.html', {'listing': listing})
