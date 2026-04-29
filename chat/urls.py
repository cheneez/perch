from django.conf import settings
from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('api/conversations/', views.conversation_list, name='conversation_list'),
    path('api/conversations/create/', views.conversation_create, name='conversation_create'),
    path('api/conversations/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('api/conversations/<int:conversation_id>/participants/', views.conversation_participants_add, name='conversation_participants_add'),
    path('api/conversations/<int:conversation_id>/participants/<int:user_id>/', views.conversation_participant_remove, name='conversation_participant_remove'),
    path('api/conversations/<int:conversation_id>/', views.conversation_update, name='conversation_update'),
    path('api/conversations/<int:conversation_id>/delete/', views.conversation_delete, name='conversation_delete'),
    path('api/users/search/', views.user_search, name='user_search'),
]

if settings.DEBUG:
    from .dev_views import dev_login
    urlpatterns += [
        path('dev-login/<int:user_id>/', dev_login, name='dev_login'),
    ]
