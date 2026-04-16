"""
Development-only views for testing chat.
These should NEVER be used in production.
"""
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.shortcuts import redirect


def dev_login(request, user_id):
    """
    GET /chat/dev-login/<user_id>/
    Instantly logs in as the given user. DEBUG mode only.
    """
    if not settings.DEBUG:
        raise Http404

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponse(f'User {user_id} not found', status=404)

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('/student/messages/')
