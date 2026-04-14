from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Favorite, Profile
from accounts.public_profile import (
    toggle_public_profile_favorite,
    try_resolve_public_profile,
)

from .forms import LessorCreateProfileForm, LessorEditDetailsForm, LessorEditProfileForm
from .models import LessorProfile


class LessorProfileRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_staff or request.user.is_superuser:
            return redirect(reverse('admin:index'))
        if Profile.objects.filter(user=request.user, user_type='admin').exists():
            return redirect(reverse('admin:index'))
        if not LessorProfile.objects.filter(user=request.user).exists():
            return redirect('lessor:create_profile')
        return super().dispatch(request, *args, **kwargs)


class LessorDashboardView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class LessorPlaceholderView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/placeholder_page.html'
    page_title = 'Page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = self.kwargs.get('page_title', self.page_title)
        return context


class LessorVerificationPlaceholderView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    """Read-only verification status for feature card link."""

    required_role = 'lessor'
    template_name = 'lessor/verification_status.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        ctx['p'] = get_object_or_404(LessorProfile, user=self.request.user)
        return ctx


class LessorCreateProfileView(RoleRequiredMixin, FormView):
    required_role = 'lessor'
    template_name = 'lessor/create_profile.html'
    form_class = LessorCreateProfileForm
    success_url = reverse_lazy('lessor:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if LessorProfile.objects.filter(user=request.user).exists():
            return redirect('lessor:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        u = self.request.user
        return {
            'first_name': u.first_name or '',
            'last_name': u.last_name or '',
            'email': u.email or '',
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        return ctx

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.user = self.request.user
        profile.username = self.request.user.username
        profile.save()
        u = self.request.user
        u.first_name = profile.first_name
        u.last_name = profile.last_name
        if profile.email:
            u.email = profile.email.strip().lower()
        u.save(update_fields=['first_name', 'last_name', 'email'])
        messages.success(self.request, 'Your profile has been created.')
        return redirect('lessor:dashboard')


class LessorProfileSelfView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/profile_self.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = get_object_or_404(LessorProfile, user=self.request.user)
        ctx['user'] = self.request.user
        ctx['p'] = profile
        ctx['top_contacts'] = self._top_contacts_self(profile)
        return ctx

    def _top_contacts_self(self, profile):
        order = [
            ('email', profile.email, 'bi-envelope', 'Email'),
            ('phone', profile.phone_number, 'bi-telephone', 'Phone'),
            ('instagram', profile.instagram, 'bi-instagram', 'Instagram'),
            ('linkedin', profile.linkedin, 'bi-linkedin', 'LinkedIn'),
            ('handshake', profile.handshake, 'bi-mortarboard', 'Handshake'),
            ('facebook', profile.facebook, 'bi-facebook', 'Facebook'),
        ]
        out = []
        for _key, val, icon, label in order:
            if val:
                out.append({'value': val, 'icon': icon, 'label': label})
            if len(out) >= 3:
                break
        return out


class LessorProfileOtherView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'lessor/public_profile.html'

    def dispatch(self, request, *args, **kwargs):
        if int(kwargs['user_id']) == request.user.id:
            return redirect('lessor:profile')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        uid = int(kwargs['user_id'])
        data = try_resolve_public_profile(uid)
        if data is None:
            return redirect('lessor:profile')
        self._public_profile_data = data
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uid = int(self.kwargs['user_id'])
        data = self._public_profile_data
        ctx['user'] = self.request.user
        ctx['profile_user'] = data.profile_user
        ctx['p'] = data.p
        ctx['profile_role'] = data.profile_role
        ctx['top_contacts'] = data.top_contacts
        ctx['hobby_labels'] = data.hobby_labels
        ctx['sections'] = data.sections
        ctx['is_favorited'] = Favorite.objects.filter(
            user=self.request.user,
            favorited_user_id=uid,
        ).exists()
        ctx['favorite_toggle_url'] = reverse(
            'lessor:public_profile_favorite',
            kwargs={'user_id': uid},
        )
        return ctx


class LessorPublicProfileFavoriteToggleView(LessorProfileRequiredMixin, RoleRequiredMixin, View):
    required_role = 'lessor'
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        return toggle_public_profile_favorite(request, int(kwargs['user_id']))


class LessorEditProfileView(LessorProfileRequiredMixin, RoleRequiredMixin, FormView):
    required_role = 'lessor'
    template_name = 'lessor/edit_profile.html'
    form_class = LessorEditProfileForm
    success_url = reverse_lazy('lessor:profile')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'] = get_object_or_404(LessorProfile, user=self.request.user)
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        p = get_object_or_404(LessorProfile, user=self.request.user)
        ctx['p'] = p
        ctx['preview_picture_url'] = p.profile_picture.url if p.profile_picture else ''
        return ctx

    def form_valid(self, form):
        profile = form.save()
        u = self.request.user
        if profile.email:
            u.email = profile.email.strip().lower()
            u.save(update_fields=['email'])
        messages.success(self.request, 'Your public profile has been updated.')
        return redirect('lessor:profile')


class LessorEditDetailsView(LessorProfileRequiredMixin, RoleRequiredMixin, FormView):
    required_role = 'lessor'
    template_name = 'lessor/edit_details.html'
    form_class = LessorEditDetailsForm
    success_url = reverse_lazy('lessor:profile')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'] = get_object_or_404(LessorProfile, user=self.request.user)
        kw['user'] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your details have been updated.')
        return redirect('lessor:profile')
