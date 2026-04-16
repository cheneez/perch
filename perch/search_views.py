from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from accounts.models import Profile
from lessor.models import LessorProfile
from student.models import StudentProfile


def _name_query(q: str) -> Q:
    q = q.strip()
    if not q:
        return Q(pk__in=[])
    tokens = q.split()
    combined = (
        Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(username__icontains=q)
    )
    if len(tokens) >= 2:
        combined |= Q(
            first_name__icontains=tokens[0],
            last_name__icontains=tokens[-1],
        )
    return combined


@login_required(login_url='/auth/login/')
def user_search(request):
    """Search users by name (first, last, username) across students + lessors."""
    q = (request.GET.get('q') or '').strip()

    results = []
    if len(q) >= 2:
        name_filter = _name_query(q)
        active = Q(account_status=Profile.AccountStatus.ACTIVE)

        student_ids = Profile.objects.filter(user_type='student').filter(active).values_list(
            'user_id',
            flat=True,
        )
        lessor_ids = Profile.objects.filter(user_type='realtor').filter(active).values_list(
            'user_id',
            flat=True,
        )

        student_qs = (
            StudentProfile.objects.filter(user_id__in=student_ids)
            .filter(name_filter)
            .exclude(user=request.user)
            .select_related('user')
            .order_by('first_name', 'last_name')[:25]
        )
        lessor_qs = (
            LessorProfile.objects.filter(user_id__in=lessor_ids)
            .filter(name_filter)
            .exclude(user=request.user)
            .select_related('user')
            .order_by('first_name', 'last_name')[:25]
        )

        results = (
            [{'kind': 'student', 'p': row} for row in student_qs]
            + [{'kind': 'lessor', 'p': row} for row in lessor_qs]
        )
        results.sort(key=lambda r: ((r['p'].first_name or '').lower(), (r['p'].last_name or '').lower()))
        results = results[:50]

    return render(
        request,
        'search/users.html',
        {
            'q': q,
            'results': results,
            'search_too_short': bool(q) and len(q) < 2,
        },
    )


@login_required(login_url='/auth/login/')
def user_profile(request, user_id: int):
    """View another user's profile cross-role (public fields only)."""
    if user_id == request.user.id:
        raise Http404()

    prof = Profile.objects.filter(user_id=user_id).first()
    if not prof or prof.account_status != Profile.AccountStatus.ACTIVE:
        raise Http404()

    if prof.user_type == 'student':
        p = get_object_or_404(StudentProfile.objects.select_related('user'), user_id=user_id)
        top = []
        checks = [
            (p.show_email, p.email, 'bi-envelope', 'Email'),
            (p.show_phone, p.phone_number, 'bi-telephone', 'Phone'),
            (p.show_instagram, p.instagram, 'bi-instagram', 'Instagram'),
            (p.show_linkedin, p.linkedin, 'bi-linkedin', 'LinkedIn'),
            (p.show_handshake, p.handshake, 'bi-mortarboard', 'Handshake'),
            (p.show_facebook, p.facebook, 'bi-facebook', 'Facebook'),
        ]
        for vis, val, icon, label in checks:
            if vis and val:
                top.append({'value': val, 'icon': icon, 'label': label})
            if len(top) >= 3:
                break
        return render(request, 'search/profile_student.html', {'p': p, 'top_contacts': top})

    if prof.user_type == 'realtor':
        p = get_object_or_404(LessorProfile.objects.select_related('user'), user_id=user_id)
        top = []
        checks = [
            (p.show_email, p.email, 'bi-envelope', 'Email'),
            (p.show_phone, p.phone_number, 'bi-telephone', 'Phone'),
            (p.show_instagram, p.instagram, 'bi-instagram', 'Instagram'),
            (p.show_linkedin, p.linkedin, 'bi-linkedin', 'LinkedIn'),
            (p.show_handshake, p.handshake, 'bi-mortarboard', 'Handshake'),
            (p.show_facebook, p.facebook, 'bi-facebook', 'Facebook'),
        ]
        for vis, val, icon, label in checks:
            if vis and val:
                top.append({'value': val, 'icon': icon, 'label': label})
            if len(top) >= 3:
                break
        return render(request, 'search/profile_lessor.html', {'p': p, 'top_contacts': top})

    raise Http404()
