from django.urls import path
from . import views

urlpatterns = [
    path('', views.listings_list, name='listings-list'),
    path('create/', views.create_listing, name='listings-create'),
    path('<int:pk>/', views.listing_detail, name='listing-detail'),
    path('<int:pk>/edit/', views.edit_listing, name='listing-edit'),
    path('<int:pk>/delete/', views.delete_listing, name='listing-delete'),
    path('detail/<int:pk>/', views.property_detail, name='listing-detail-legacy'),
    path('property/<int:pk>/', views.property_detail, name='property'),
    path('property/<int:pk>/contact/', views.contact_realtor, name='property-contact'),
]
app_name = 'listings'
