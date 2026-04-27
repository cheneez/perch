from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required(login_url='/auth/login/')
def notification_list(request):
    qs = Notification.objects.filter(recipient=request.user)
    return render(
        request,
        'notifications/list.html',
        {
            'notifications': qs[:100],
            'unread_count': qs.filter(read_at__isnull=True).count(),
        },
    )


@login_required(login_url='/auth/login/')
@require_POST
def mark_all_read(request):
    Notification.objects.filter(
        recipient=request.user,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    return redirect('notifications:list')

