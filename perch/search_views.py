from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

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
    viewer_profile = Profile.objects.filter(user=request.user).first()
    viewer_profile_namespace = 'lessor' if viewer_profile and viewer_profile.user_type in ('realtor', 'lessor') else 'student'

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
            'viewer_profile_namespace': viewer_profile_namespace,
        },
    )
