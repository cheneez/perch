from django.urls import path
from . import views

urlpatterns = [
    path('', views.listings_list, name='listings-list'),
    path('create/', views.create_listing, name='listings-create'),
    path('detail/', views.listing_detail, name='listing-detail')

]