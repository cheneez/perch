from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
]
