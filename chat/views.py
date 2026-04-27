import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Profile
from lessor.models import LessorProfile
from .models import Conversation, Message

User = get_user_model()

MAX_GROUP_SIZE = 10


def _broadcast_participant_update(conv, action, changed_user):
    channel_layer = get_channel_layer()
    participants = list(conv.participants.all())
    profile_cache = {
        p.user_id: p.user_type
        for p in Profile.objects.filter(user_id__in=[u.id for u in participants])
    }
    async_to_sync(channel_layer.group_send)(
        f'chat_{conv.id}',
        {
            'type': 'participant_update',
            'action': action,
            'user_id': changed_user.id,
            'user_name': changed_user.get_full_name() or changed_user.username,
            'participants': [_participant_data(u, None, profile_cache) for u in participants],
        },
    )


def _chat_user_required(view_func):
    """Decorator: user must be authenticated and have a student or realtor profile."""
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.user_type not in ('student', 'realtor'):
                return JsonResponse({'error': 'Chat not available for this account type'}, status=403)
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found'}, status=403)
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _participant_data(user, current_user_id, profile_cache=None):
    name = user.get_full_name() or user.username
    initials = ''.join(p[0].upper() for p in name.split()[:2]) if name else '?'
    if profile_cache is not None:
        user_type = profile_cache.get(user.id, 'unknown')
    else:
        try:
            user_type = Profile.objects.get(user=user).user_type
        except Profile.DoesNotExist:
            user_type = 'unknown'
    return {
        'id': user.id,
        'name': name,
        'user_type': user_type,
        'initials': initials,
        'is_self': user.id == current_user_id,
    }


@_chat_user_required
@require_GET
def conversation_list(request):
    """GET /chat/api/conversations/"""
    conversations = (
        Conversation.objects
        .filter(participants=request.user)
        .prefetch_related('participants')
        .order_by('-updated_at')
    )

    results = []
    for conv in conversations:
        participants = list(conv.participants.all())
        participant_ids = [u.id for u in participants]
        profile_cache = {
            p.user_id: p.user_type
            for p in Profile.objects.filter(user_id__in=participant_ids)
        }

        last_msg = conv.messages.select_related('sender').order_by('-created_at').first()

        results.append({
            'id': conv.id,
            'name': conv.name,
            'is_group': conv.is_group,
            'created_by_id': conv.created_by_id,
            'participants': [_participant_data(u, request.user.id, profile_cache) for u in participants],
            'last_message': {
                'content': last_msg.content if last_msg else None,
                'sender_id': last_msg.sender_id if last_msg else None,
                'sender_name': (last_msg.sender.get_full_name() or last_msg.sender.username) if last_msg else None,
                'timestamp': last_msg.created_at.isoformat() if last_msg else None,
            },
            'updated_at': conv.updated_at.isoformat(),
        })

    return JsonResponse({'conversations': results})


@_chat_user_required
@require_POST
def conversation_create(request):
    """
    POST /chat/api/conversations/create/
    Body: {"user_ids": [int, ...], "name": "optional group name"}
    1 user_id  → 1:1 DM (de-duplicated)
    2+ user_ids → group chat
    """
    try:
        data = json.loads(request.body)
        user_ids = [int(uid) for uid in data['user_ids']]
        group_name = data.get('name', '').strip()
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'Provide a valid user_ids list'}, status=400)

    if not user_ids:
        return JsonResponse({'error': 'user_ids must not be empty'}, status=400)
    if len(user_ids) >= MAX_GROUP_SIZE:
        return JsonResponse({'error': f'Maximum {MAX_GROUP_SIZE - 1} other participants'}, status=400)
    if request.user.id in user_ids:
        return JsonResponse({'error': 'Cannot include yourself'}, status=400)

    target_users = []
    for uid in user_ids:
        try:
            u = User.objects.get(id=uid)
            profile = Profile.objects.get(user=u)
            if profile.user_type not in ('student', 'realtor'):
                return JsonResponse({'error': f'User {uid} cannot use chat'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': f'User {uid} not found'}, status=404)
        except Profile.DoesNotExist:
            return JsonResponse({'error': f'User {uid} not found'}, status=404)
        target_users.append(u)

    is_group = len(user_ids) > 1 or bool(group_name)

    if not is_group:
        existing = (
            Conversation.objects
            .filter(participants=request.user)
            .filter(participants=target_users[0])
            .filter(is_group=False)
            .first()
        )
        if existing:
            return JsonResponse({'conversation': {'id': existing.id, 'created': False}})

    conv = Conversation.objects.create(
        name=group_name,
        is_group=is_group,
        created_by=request.user,
    )
    conv.participants.add(request.user, *target_users)

    return JsonResponse({'conversation': {'id': conv.id, 'created': True}}, status=201)


@_chat_user_required
@require_GET
def conversation_messages(request, conversation_id):
    """GET /chat/api/conversations/<id>/messages/"""
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

    messages_qs = messages_qs.order_by('-created_at')[:50]
    messages_list = list(reversed(list(messages_qs)))

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


@_chat_user_required
def conversation_participants_add(request, conversation_id):
    """POST /chat/api/conversations/<id>/participants/ — add members (creator only)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        conv = Conversation.objects.get(id=conversation_id, participants=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

    if conv.created_by_id != request.user.id:
        return JsonResponse({'error': 'Only the creator can add members'}, status=403)

    try:
        data = json.loads(request.body)
        user_ids = [int(uid) for uid in data['user_ids']]
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'Provide a valid user_ids list'}, status=400)

    current_count = conv.participants.count()
    if current_count + len(user_ids) > MAX_GROUP_SIZE:
        return JsonResponse({'error': f'Would exceed maximum group size of {MAX_GROUP_SIZE}'}, status=400)

    added = []
    for uid in user_ids:
        try:
            u = User.objects.get(id=uid)
            profile = Profile.objects.get(user=u)
            if profile.user_type not in ('student', 'realtor'):
                continue
            conv.participants.add(u)
            added.append(uid)
        except (User.DoesNotExist, Profile.DoesNotExist):
            pass

    if not conv.is_group and conv.participants.count() > 2:
        conv.is_group = True
        conv.save(update_fields=['is_group'])

    for uid in added:
        try:
            _broadcast_participant_update(conv, 'added', User.objects.get(id=uid))
        except User.DoesNotExist:
            pass

    return JsonResponse({'added': added})


@_chat_user_required
def conversation_participant_remove(request, conversation_id, user_id):
    """DELETE /chat/api/conversations/<id>/participants/<user_id>/"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        conv = Conversation.objects.get(id=conversation_id, participants=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

    is_self = user_id == request.user.id
    is_creator = conv.created_by_id == request.user.id

    if not is_self and not is_creator:
        return JsonResponse({'error': 'Only the creator can remove others'}, status=403)

    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    conv.participants.remove(target)
    _broadcast_participant_update(conv, 'removed', target)
    return JsonResponse({'removed': user_id})


@_chat_user_required
def conversation_update(request, conversation_id):
    """PATCH /chat/api/conversations/<id>/ — rename (creator only)"""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        conv = Conversation.objects.get(id=conversation_id, participants=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

    if conv.created_by_id != request.user.id:
        return JsonResponse({'error': 'Only the creator can rename this conversation'}, status=403)

    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    conv.name = new_name[:100]
    conv.save(update_fields=['name'])
    return JsonResponse({'name': conv.name})


@_chat_user_required
@require_GET
def user_search(request):
    """
    GET /chat/api/users/search/?q=<query>&type=all|student|lessor
    Search chat-eligible users by name or email. Returns up to 20 results.
    """
    query = request.GET.get('q', '').strip()
    filter_type = request.GET.get('type', 'all')

    if len(query) < 2:
        return JsonResponse({'users': []})

    eligible_ids = set()

    if filter_type in ('all', 'student'):
        student_ids = Profile.objects.filter(
            user_type='student',
            email_verified=True,
        ).exclude(user=request.user).values_list('user_id', flat=True)
        eligible_ids.update(student_ids)

    if filter_type in ('all', 'lessor'):
        lessor_ids = LessorProfile.objects.filter(
            verified=True,
        ).exclude(user=request.user).values_list('user_id', flat=True)
        eligible_ids.update(lessor_ids)

    users = (
        User.objects
        .filter(id__in=eligible_ids)
        .filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
        [:20]
    )

    profile_cache = {
        p.user_id: p.user_type
        for p in Profile.objects.filter(user_id__in=[u.id for u in users])
    }

    results = [
        {
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'email': u.email,
            'user_type': profile_cache.get(u.id, 'unknown'),
        }
        for u in users
    ]

    return JsonResponse({'users': results})
