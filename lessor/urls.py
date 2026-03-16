from django.urls import path
from . import views

app_name = 'lessor'

urlpatterns = [
    path('dashboard/', views.LessorDashboardView.as_view(), name='dashboard'),
]
