from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('property/<int:pk>/', views.property_detail, name='property'),
]