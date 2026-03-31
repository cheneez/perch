from accounts.models import Profile
from lessor.models import LessorProfile
from student.models import StudentProfile


def user_profile_context(request):
    if not request.user.is_authenticated:
        return {'user_profile': None, 'account_user_type': None}
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'student'},
    )
    ut = profile.user_type
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
