from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile

from .forms import LessorCreateProfileForm, LessorEditDetailsForm, LessorEditProfileForm
from .models import LessorProfile


class LessorProfileRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
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
    template_name = 'lessor/profile_other.html'

    def dispatch(self, request, *args, **kwargs):
        if int(kwargs['user_id']) == request.user.id:
            return redirect('lessor:profile')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uid = self.kwargs['user_id']
        target = get_object_or_404(LessorProfile.objects.select_related('user'), user_id=uid)
        acc = Profile.objects.filter(user_id=uid).first()
        if not acc or acc.user_type not in ('realtor', 'lessor'):
            raise Http404()
        ctx['user'] = self.request.user
        ctx['p'] = target
        ctx['top_contacts'] = self._top_contacts_public(target)
        ctx['sections'] = self._section_flags(target)
        return ctx

    def _top_contacts_public(self, profile):
        checks = [
            (profile.show_email, profile.email, 'bi-envelope', 'Email'),
            (profile.show_phone, profile.phone_number, 'bi-telephone', 'Phone'),
            (profile.show_instagram, profile.instagram, 'bi-instagram', 'Instagram'),
            (profile.show_linkedin, profile.linkedin, 'bi-linkedin', 'LinkedIn'),
            (profile.show_handshake, profile.handshake, 'bi-mortarboard', 'Handshake'),
            (profile.show_facebook, profile.facebook, 'bi-facebook', 'Facebook'),
        ]
        out = []
        for visible, val, icon, label in checks:
            if visible and val:
                out.append({'value': val, 'icon': icon, 'label': label})
            if len(out) >= 3:
                break
        return out

    def _section_flags(self, p):
        about = any(
            [
                p.display_name,
                p.bio,
                p.fun_fact_1,
                p.fun_fact_2,
                p.fun_fact_3,
            ]
        )
        social_rows = []
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
                social_rows.append({'value': val, 'icon': icon, 'label': label})
        return {
            'about': about,
            'social': bool(social_rows),
            'social_rows': social_rows,
        }


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
