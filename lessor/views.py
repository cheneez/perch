from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class LessorDashboardView(RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class LessorPlaceholderView(RoleRequiredMixin, TemplateView):
    """Placeholder for lessor pages (messages, create listing, etc.)."""
    required_role = 'lessor'
    template_name = 'lessor/placeholder_page.html'
    page_title = 'Page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = self.kwargs.get('page_title', self.page_title)
        return context
