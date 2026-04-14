from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View

from django.urls import reverse

from .models import get_or_create_account_profile


class RoleRequiredMixin(LoginRequiredMixin):
    login_url = reverse_lazy('login')
    """Restrict view to a given role. Set required_role to 'student' or 'lessor'."""
    required_role = None  # 'student' or 'lessor'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile, _ = get_or_create_account_profile(request.user)
        if profile.user_type == 'admin' or request.user.is_staff:
            return redirect(reverse('admin:index'))
        if not profile.email_verified:
            return redirect('verify')
        user_type = profile.user_type
        if self.required_role == 'student':
            if user_type != 'student':
                return redirect('lessor:dashboard')
        elif self.required_role == 'lessor':
            if user_type not in ('realtor', 'lessor'):
                return redirect('student:dashboard')
        return super().dispatch(request, *args, **kwargs)
