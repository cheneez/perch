from django.urls import path

from . import views

app_name = 'lessor'

urlpatterns = [
    path('create-profile/', views.LessorCreateProfileView.as_view(), name='create_profile'),
    path('dashboard/', views.LessorDashboardView.as_view(), name='dashboard'),
    path('messages/', views.LessorPlaceholderView.as_view(), {'page_title': 'Messages'}, name='messages'),
    path('create-listing/', views.LessorPlaceholderView.as_view(), {'page_title': 'Create listing'}, name='create_listing'),
    path('listings/', views.LessorPlaceholderView.as_view(), {'page_title': 'View listings'}, name='view_listings'),
    path('find-tenants/', views.LessorPlaceholderView.as_view(), {'page_title': 'Find tenants'}, name='find_tenants'),
    path('verification/', views.LessorVerificationPlaceholderView.as_view(), name='verification'),
    path('profile/', views.LessorProfileSelfView.as_view(), name='profile'),
    path('profile/<int:user_id>/', views.LessorProfileOtherView.as_view(), name='public_profile'),
    path(
        'profile/<int:user_id>/favorite/',
        views.LessorPublicProfileFavoriteToggleView.as_view(),
        name='public_profile_favorite',
    ),
    path('edit-profile/', views.LessorEditProfileView.as_view(), name='edit_profile'),
    path('edit-details/', views.LessorEditDetailsView.as_view(), name='edit_details'),
]
