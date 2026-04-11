from accounts.models import get_or_create_account_profile
from lessor.models import LessorProfile
from student.models import StudentProfile


def user_profile_context(request):
    if not request.user.is_authenticated:
        return {'user_profile': None, 'account_user_type': None}
    profile, _ = get_or_create_account_profile(request.user)
    ut = profile.user_type
    if ut == 'admin' or request.user.is_staff:
        return {'user_profile': None, 'account_user_type': 'admin'}
    if ut == 'student':
        try:
            return {
                'user_profile': request.user.student_profile,
                'account_user_type': ut,
            }
        except StudentProfile.DoesNotExist:
            return {'user_profile': None, 'account_user_type': ut}
    try:
        return {
            'user_profile': request.user.leasor_profile,
            'account_user_type': ut,
        }
    except LessorProfile.DoesNotExist:
        return {'user_profile': None, 'account_user_type': ut}
