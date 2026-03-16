from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Listing


@login_required
def property_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, 'listings/property.html', {'listing': listing})
