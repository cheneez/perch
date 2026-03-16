from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('google/start/', views.google_start_view, name='google_start'),
    path('google/callback/', views.google_callback_view, name='google_callback'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/', views.verify_view, name='verify'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
