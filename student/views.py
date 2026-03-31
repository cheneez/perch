import json

from django.views.generic import TemplateView, View
from django.shortcuts import render

from accounts.mixins import RoleRequiredMixin
from listings.models import Listing


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class FindHousingView(View):

    def get(self, request):
        qs = Listing.objects.filter(status='available').prefetch_related('images')

        min_price = request.GET.get('min_price', '').strip()
        max_price = request.GET.get('max_price', '').strip()
        bedrooms  = request.GET.get('bedrooms', '').strip()
        room_type = request.GET.get('room_type', '').strip()

        if min_price:
            qs = qs.filter(price_monthly__gte=min_price)
        if max_price:
            qs = qs.filter(price_monthly__lte=max_price)
        if bedrooms:
            qs = qs.filter(bedrooms=bedrooms)
        if room_type:
            qs = qs.filter(room_type=room_type)

        qs = qs.order_by('-created_at')

        map_pins = json.dumps([
            {
                'pk': l.pk,
                'lat': l.latitude,
                'lng': l.longitude,
                'title': l.title,
                'price': str(l.price_monthly),
            }
            for l in qs if l.latitude is not None and l.longitude is not None
        ])

        return render(request, 'student/find_housing.html', {
            'listings': qs,
            'map_pins': map_pins,
            'filters': request.GET,
        })


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
