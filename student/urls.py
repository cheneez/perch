from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    path('messages/', views.StudentPlaceholderView.as_view(), {'page_title': 'Messages'}, name='messages'),
    path('groups/', views.StudentPlaceholderView.as_view(), {'page_title': 'Groups'}, name='groups'),
    path('roommates/', views.StudentPlaceholderView.as_view(), {'page_title': 'Roommates'}, name='roommates'),
    path('find-housing/', views.StudentPlaceholderView.as_view(), {'page_title': 'Find Housing'}, name='find_housing'),
    path('profile/', views.StudentPlaceholderView.as_view(), {'page_title': 'My profile'}, name='profile'),
]
