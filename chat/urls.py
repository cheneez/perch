from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('api/conversations/', views.conversation_list, name='conversation_list'),
    path('api/conversations/create/', views.conversation_create, name='conversation_create'),
    path('api/conversations/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('api/students/search/', views.student_search, name='student_search'),
]
