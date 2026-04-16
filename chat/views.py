import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Profile
from .models import Conversation, Message


def _student_required(view_func):
    """Decorator: user must be authenticated and have a student profile."""
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.user_type != 'student':
                return JsonResponse({'error': 'Students only'}, status=403)
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found'}, status=403)
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


@_student_required
@require_GET
def conversation_list(request):
    """
    GET /chat/api/conversations/
    Returns the current user's conversations, sorted by most recent activity.
    Each entry includes the other participant's info and the last message.
    """
    conversations = (
        Conversation.objects
        .filter(participants=request.user)
        .annotate(last_message_time=Max('messages__created_at'))
        .order_by('-updated_at')
    )

    results = []
    for conv in conversations:
        other_users = conv.participants.exclude(id=request.user.id)
        other = other_users.first()

        last_msg = conv.messages.order_by('-created_at').first()

        results.append({
            'id': conv.id,
            'other_user': {
                'id': other.id if other else None,
                'name': (other.get_full_name() or other.username) if other else 'Unknown',
                'first_name': other.first_name if other else '',
                'last_name': other.last_name if other else '',
            } if other else None,
            'last_message': {
                'content': last_msg.content if last_msg else None,
                'sender_id': last_msg.sender_id if last_msg else None,
                'timestamp': last_msg.created_at.isoformat() if last_msg else None,
            },
            'updated_at': conv.updated_at.isoformat(),
        })

    return JsonResponse({'conversations': results})


@_student_required
@require_POST
def conversation_create(request):
    """
    POST /chat/api/conversations/create/
    Body: {"user_id": <int>}
    Creates a 1:1 conversation with the target user, or returns
    the existing one if it already exists.
    """
    try:
        data = json.loads(request.body)
        target_user_id = int(data['user_id'])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'Provide a valid user_id'}, status=400)

    if target_user_id == request.user.id:
        return JsonResponse({'error': 'Cannot message yourself'}, status=400)

    # Verify target is a student
    try:
        target_user = User.objects.get(id=target_user_id)
        target_profile = Profile.objects.get(user=target_user)
        if target_profile.user_type != 'student':
            return JsonResponse({'error': 'Target user is not a student'}, status=400)
    except (User.DoesNotExist, Profile.DoesNotExist):
        return JsonResponse({'error': 'User not found'}, status=404)

    # Check for existing 1:1 conversation between these two users
    existing = (
        Conversation.objects
        .filter(participants=request.user)
        .filter(participants=target_user)
        .first()
    )

    if existing:
        return JsonResponse({
            'conversation': {
                'id': existing.id,
                'created': False,
            }
        })

    conv = Conversation.objects.create()
    conv.participants.add(request.user, target_user)

    return JsonResponse({
        'conversation': {
            'id': conv.id,
            'created': True,
        }
    }, status=201)


@_student_required
@require_GET
def conversation_messages(request, conversation_id):
    """
    GET /chat/api/conversations/<id>/messages/
    Returns messages for a conversation (oldest first).
    Supports simple pagination via ?before=<message_id> for loading older messages.
    """
    try:
        conv = Conversation.objects.get(id=conversation_id, participants=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

    messages_qs = conv.messages.select_related('sender').order_by('created_at')

    before_id = request.GET.get('before')
    if before_id:
        try:
            messages_qs = messages_qs.filter(id__lt=int(before_id))
        except (ValueError, TypeError):
            pass

    # Return last 50 messages
    messages_qs = messages_qs.order_by('-created_at')[:50]
    messages_list = list(messages_qs)
    messages_list.reverse()  # Back to chronological order

    results = [
        {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'content': msg.content,
            'timestamp': msg.created_at.isoformat(),
        }
        for msg in messages_list
    ]

    return JsonResponse({'messages': results})


@_student_required
@require_GET
def student_search(request):
    """
    GET /chat/api/students/search/?q=<query>
    Search students by name or email. Returns up to 20 results.
    Excludes the current user.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'students': []})

    student_user_ids = Profile.objects.filter(
        user_type='student',
        email_verified=True,
    ).exclude(user=request.user).values_list('user_id', flat=True)

    users = (
        User.objects
        .filter(id__in=student_user_ids)
        .filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
        [:20]
    )

    results = [
        {
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'email': u.email,
        }
        for u in users
    ]

    return JsonResponse({'students': results})
