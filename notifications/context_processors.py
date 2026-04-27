from .models import Notification


def unread_notification_count(request):
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return {'unread_notification_count': 0}
    return {
        'unread_notification_count': Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).count()
    }

