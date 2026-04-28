from django.conf import settings
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('google/start/', views.google_start_view, name='google_start'),
    path('google/callback/', views.google_callback_view, name='google_callback'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/', views.verify_view, name='verify'),
    path('verify/resend/', views.resend_verification_view, name='verify_resend'),
    path('v/<uuid:token>/', views.verify_confirm_view, name='verify_confirm_short'),
    path('verify/confirm/<uuid:token>/', views.verify_confirm_view, name='verify_confirm'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]

#Development-only shortcut for local load testing with local Locust users (avoids Google Oauth flow).
if settings.DEBUG:
    urlpatterns += [
        path('dev-login/<str:username>/', views.dev_login_by_username, name='dev_login_by_username'),
    ]
