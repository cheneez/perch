import json

from django.conf import settings
from django.views.generic import TemplateView, View
from django.shortcuts import render


from listings.models import Listing
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

from .forms import (
    StudentCreateProfileForm,
    StudentCompatibilitySurveyForm,
    StudentEditDetailsForm,
    StudentEditProfileForm,
)
from .models import HOBBY_TAG_OPTIONS, StudentCompatibilitySurvey, StudentProfile


class StudentProfileRequiredMixin:
    """Redirect to create-profile when the student has not completed onboarding."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_staff or request.user.is_superuser:
            return redirect(reverse('admin:index'))
        if Profile.objects.filter(user=request.user, user_type='admin').exists():
            return redirect(reverse('admin:index'))
        if not StudentProfile.objects.filter(user=request.user).exists():
            return redirect('student:create_profile')
        return super().dispatch(request, *args, **kwargs)


def hobby_label_map():
    return dict(HOBBY_TAG_OPTIONS)


class StudentDashboardView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
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
        radius    = request.GET.get('radius', '1').strip()

        try:
            radius_float = float(radius)
            if radius_float not in (0.5, 1.0, 2.0, 5.0):
                raise ValueError
        except ValueError:
            radius_float = 1.0
            radius = '1'

        if min_price:
            qs = qs.filter(price_monthly__gte=min_price)
        if max_price:
            qs = qs.filter(price_monthly__lte=max_price)
        if bedrooms:
            qs = qs.filter(bedrooms=bedrooms)
        if room_type:
            qs = qs.filter(room_type=room_type)

        qs = qs.filter(distance_miles__lte=radius_float).order_by('-created_at')

        def primary_image_url(listing):
            image = listing.images.first()
            if not image:
                return ''
            if image.image:
                return image.image.url
            return image.image_url or ''

        map_pins = json.dumps([
            {
                'pk': l.pk,
                'lat': l.latitude,
                'lng': l.longitude,
                'title': l.title,
                'price': str(l.price_monthly),
                'image_url': primary_image_url(l),
                'url': reverse('listings:property', args=[l.pk]),
            }
            for l in qs if l.latitude is not None and l.longitude is not None
        ])

        return render(request, 'student/find_housing.html', {
            'listings': qs,
            'map_pins': map_pins,
            'filters': request.GET,
            'radius': radius,
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
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


class StudentCreateProfileView(RoleRequiredMixin, FormView):
    required_role = 'student'
    template_name = 'student/create_profile.html'
    form_class = StudentCreateProfileForm
    success_url = reverse_lazy('student:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if StudentProfile.objects.filter(user=request.user).exists():
            return redirect('student:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        u = self.request.user
        return {
            'first_name': u.first_name or '',
            'last_name': u.last_name or '',
            'school': 'Boston College',
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        ctx['prefill_email'] = self.request.user.email
        return ctx

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.user = self.request.user
        profile.username = self.request.user.username
        profile.email = self.request.user.email or ''
        profile.save()
        u = self.request.user
        u.first_name = profile.first_name
        u.last_name = profile.last_name
        u.save(update_fields=['first_name', 'last_name'])
        messages.success(self.request, 'Your profile has been created.')
        return redirect('student:dashboard')


class StudentProfileSelfView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/profile_self.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = get_object_or_404(StudentProfile, user=self.request.user)
        ctx['user'] = self.request.user
        ctx['p'] = profile
        ctx['top_contacts'] = self._top_contacts_self(profile)
        ctx['hobby_labels'] = hobby_label_map()
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


class StudentProfileOtherView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/public_profile.html'

    def dispatch(self, request, *args, **kwargs):
        if int(kwargs['user_id']) == request.user.id:
            return redirect('student:profile')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        uid = int(kwargs['user_id'])
        data = try_resolve_public_profile(uid)
        if data is None:
            return redirect('student:profile')
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
            'student:public_profile_favorite',
            kwargs={'user_id': uid},
        )
        return ctx


class StudentPublicProfileFavoriteToggleView(StudentProfileRequiredMixin, RoleRequiredMixin, View):
    required_role = 'student'
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        return toggle_public_profile_favorite(request, int(kwargs['user_id']))


class StudentEditProfileView(StudentProfileRequiredMixin, RoleRequiredMixin, FormView):
    required_role = 'student'
    template_name = 'student/edit_profile.html'
    form_class = StudentEditProfileForm
    success_url = reverse_lazy('student:profile')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'] = get_object_or_404(StudentProfile, user=self.request.user)
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        p = get_object_or_404(StudentProfile, user=self.request.user)
        ctx['p'] = p
        ctx['hobby_labels'] = hobby_label_map()
        ctx['hobby_labels_for_script'] = hobby_label_map()
        ctx['preview_picture_url'] = p.profile_picture.url if p.profile_picture else ''
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your public profile has been updated.')
        return redirect('student:profile')


class StudentEditDetailsView(StudentProfileRequiredMixin, RoleRequiredMixin, FormView):
    required_role = 'student'
    template_name = 'student/edit_details.html'
    form_class = StudentEditDetailsForm
    success_url = reverse_lazy('student:profile')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'] = get_object_or_404(StudentProfile, user=self.request.user)
        kw['user'] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your details have been updated.')
        return redirect('student:profile')


class CompatibilitySurveyRedirectView(StudentProfileRequiredMixin, RoleRequiredMixin, View):
    required_role = 'student'

    def get(self, request, *args, **kwargs):
        url = getattr(settings, 'COMPATIBILITY_SURVEY_URL', '').strip()
        if not url:
            messages.error(request, 'Compatibility survey is not configured yet.')
            return redirect('student:profile')
        return redirect(url)


class CompatibilitySurveyInfoView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/compatibility_survey.html'


class CompatibilitySurveyView(StudentProfileRequiredMixin, RoleRequiredMixin, FormView):
    required_role = 'student'
    template_name = 'student/compatibility_survey.html'
    form_class = StudentCompatibilitySurveyForm

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        instance = StudentCompatibilitySurvey.objects.filter(user=self.request.user).first()
        if instance:
            kw['instance'] = instance
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        # Compute and persist 5 category scores (1–5) on the StudentProfile.
        p = get_object_or_404(StudentProfile, user=self.request.user)
        s = StudentCompatibilitySurvey.score_from_choice

        personality_vals = [s(obj.personality), s(obj.guests), s(obj.noise_level)]
        living_vals = [s(obj.smoking_habits), s(obj.party_at_home), s(obj.study_at_home)]
        roommate_vals = [s(obj.roommate_relationship), s(obj.conflict_style)]
        clean_vals = [s(obj.cleanliness)]
        sleep_vals = [s(obj.sleep_schedule), s(obj.morning_night_preference)]

        def avg(vals):
            nums = [v for v in vals if v is not None]
            return (sum(nums) / len(nums)) if nums else None

        p.personality_score = avg(personality_vals)
        p.living_habits_score = avg(living_vals)
        p.roommate_preference_score = avg(roommate_vals)
        p.cleanliness_score = avg(clean_vals)
        p.sleep_score = avg(sleep_vals)
        p.save(
            update_fields=[
                'personality_score',
                'living_habits_score',
                'roommate_preference_score',
                'cleanliness_score',
                'sleep_score',
            ]
        )

        messages.success(self.request, 'Your compatibility survey was saved.')
        return redirect('student:profile')
