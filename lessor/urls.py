from django.urls import path
from . import views

app_name = 'lessor'

urlpatterns = [
    path('dashboard/', views.LessorDashboardView.as_view(), name='dashboard'),
    path('messages/', views.LessorPlaceholderView.as_view(), {'page_title': 'Messages'}, name='messages'),
    path('create-listing/', views.LessorPlaceholderView.as_view(), {'page_title': 'Create listing'}, name='create_listing'),
    path('listings/', views.LessorPlaceholderView.as_view(), {'page_title': 'View listings'}, name='view_listings'),
    path('find-tenants/', views.LessorPlaceholderView.as_view(), {'page_title': 'Find tenants'}, name='find_tenants'),
    path('profile/', views.LessorPlaceholderView.as_view(), {'page_title': 'My profile'}, name='profile'),
]
