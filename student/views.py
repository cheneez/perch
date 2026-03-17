from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class StudentPlaceholderView(RoleRequiredMixin, TemplateView):
    """Placeholder for student pages (messages, groups, roommates, etc.)."""
    required_role = 'student'
    template_name = 'student/placeholder_page.html'
    page_title = 'Page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = self.kwargs.get('page_title', self.page_title)
        return context
