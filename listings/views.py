from django.shortcuts import render

# Create your views here.
def create_listing(request):
    return render(request, "listings/create.html")

def listings_list(request):
    return render(request, "listings/list.html")
    
def listing_detail(request):
    return render(request, "listings/detail.html")
