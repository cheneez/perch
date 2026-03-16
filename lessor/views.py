from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class LessorDashboardView(RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
