from django.urls import path

from . import views

app_name = 'student'

urlpatterns = [
    path('create-profile/', views.StudentCreateProfileView.as_view(), name='create_profile'),
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    path('messages/', views.StudentPlaceholderView.as_view(), {'page_title': 'Messages'}, name='messages'),
    path('groups/', views.StudentPlaceholderView.as_view(), {'page_title': 'Groups'}, name='groups'),
    path('roommates/', views.StudentPlaceholderView.as_view(), {'page_title': 'Roommates'}, name='roommates'),
    path('find-housing/', views.FindHousingView.as_view(), name='find_housing'),
    path('profile/', views.StudentProfileSelfView.as_view(), name='profile'),
    path('profile/<int:user_id>/', views.StudentProfileOtherView.as_view(), name='profile_other'),
    path('edit-profile/', views.StudentEditProfileView.as_view(), name='edit_profile'),
    path('edit-details/', views.StudentEditDetailsView.as_view(), name='edit_details'),
    path('compatibility/', views.CompatibilitySurveyRedirectView.as_view(), name='compatibility'),
    path('compatibility-survey/', views.CompatibilitySurveyView.as_view(), name='compatibility_survey'),
]
