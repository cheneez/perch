import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import render


from listings.models import Listing, ListingFavorite
from chat.models import Conversation, Message
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView
from django.views.decorators.http import require_POST

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
from .compatibility import compatibility_percent
from .models import (
    GRADUATION_YEAR_CHOICES,
    MAJOR_CHOICES,
    HOBBY_TAG_OPTIONS,
    StudentCompatibilitySurvey,
    StudentProfile,
)


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

    @staticmethod
    def get_completed_survey(user):
        survey = StudentCompatibilitySurvey.objects.filter(user=user).first()
        if survey and survey.is_completed():
            return survey
        return None


def hobby_label_map():
    return dict(HOBBY_TAG_OPTIONS)


class StudentDashboardView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        user = self.request.user
        context['favorite_listings'] = (
            Listing.objects.accessible_to(self.request.user)
            .filter(favorited_by__user=user, status='available')
            .prefetch_related('images')
            .distinct()
            .order_by('-favorited_by__created_at')[:12]
        )
        context['favorite_listing_ids'] = set(
            ListingFavorite.objects.filter(user=user).values_list('listing_id', flat=True)
        )
        # Recent chat previews for dashboard Chat section.
        conversations = (
            Conversation.objects
            .filter(participants=user)
            .annotate(last_message_time=Max('messages__created_at'))
            .order_by('-updated_at')[:5]
        )
        preview_items = []
        for conv in conversations:
            other = conv.participants.exclude(id=user.id).first()
            last_msg = conv.messages.order_by('-created_at').first()
            if not other or not last_msg:
                continue
            preview_items.append(
                {
                    "id": conv.id,
                    "other_name": other.get_full_name() or other.username,
                    "last_snippet": last_msg.content[:80],
                    "timestamp": last_msg.created_at,
                }
            )
        context["recent_conversations"] = preview_items
        return context


class FindHousingView(View):

    def get(self, request):
        qs = (
            Listing.objects.publicly_visible()
            .filter(status=Listing.Status.AVAILABLE)
            .prefetch_related('images')
        )

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
        favorite_listing_ids = set(
            ListingFavorite.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

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
            'favorite_listing_ids': favorite_listing_ids,
        })


@login_required
@require_POST
def toggle_listing_favorite(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.publicly_visible().filter(status='available'),
        pk=listing_id,
    )
    favorite, created = ListingFavorite.objects.get_or_create(
        user=request.user,
        listing=listing,
    )
    if not created:
        favorite.delete()
    return redirect(request.POST.get('next') or reverse('student:find_housing'))


class StudentMessagesView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    """Real-time messaging page for students."""
    required_role = 'student'
    template_name = 'chat/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class StudentPlaceholderView(RoleRequiredMixin, TemplateView):
    """Placeholder for student pages (groups, roommates, etc.)."""
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
        survey = self.get_completed_survey(self.request.user)
        ctx['user'] = self.request.user
        ctx['p'] = profile
        ctx['top_contacts'] = self._top_contacts_self(profile)
        ctx['hobby_labels'] = hobby_label_map()
        ctx['has_completed_survey'] = bool(survey)
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

        messages.success(self.request, 'Your compatibility survey was saved.')
        return redirect('student:profile')


class FindRoommatesView(StudentProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'student'
    template_name = 'student/find_roommates.html'

    FILTER_FIELDS = ('graduation_year', 'major', 'smoking_habits', 'cleanliness', 'noise_level', 'sleep_schedule')

    def dispatch(self, request, *args, **kwargs):
        self.viewer_survey = self.get_completed_survey(request.user)
        if not self.viewer_survey:
            messages.info(request, 'Complete your compatibility survey first to find roommates.')
            return redirect('student:compatibility_survey')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filters = {name: self.request.GET.get(name, '').strip() for name in self.FILTER_FIELDS}
        candidates = self._eligible_candidates(filters)
        has_filters = any(filters.values())
        base_pool_count = self._base_candidate_count()

        results = []
        for candidate in candidates:
            candidate_survey = candidate.compatibility_survey
            score = compatibility_percent(self.viewer_survey, candidate_survey)
            results.append(
                {
                    'user_id': candidate.id,
                    'name': self._privacy_name(candidate),
                    'avatar_url': (
                        candidate.student_profile.profile_picture.url
                        if candidate.student_profile and candidate.student_profile.profile_picture
                        else ''
                    ),
                    'gender': candidate.student_profile.get_gender_identity_display()
                    if candidate.student_profile and candidate.student_profile.gender_identity
                    else '',
                    'graduation_year': candidate_survey.get_graduation_year_display(),
                    'major': candidate_survey.get_major_display(),
                    'compatibility_score': score,
                }
            )
        results.sort(key=lambda item: item['compatibility_score'], reverse=True)

        ctx.update(
            {
                'user': self.request.user,
                'results': results,
                'filters': filters,
                'graduation_year_choices': GRADUATION_YEAR_CHOICES,
                'major_choices': MAJOR_CHOICES,
                'empty_no_candidates': base_pool_count == 0,
                'empty_no_matches': base_pool_count > 0 and len(results) == 0,
                'has_filters': has_filters,
            }
        )
        return ctx

    def _eligible_candidates(self, filters):
        qs = (
            User.objects.select_related('student_profile', 'compatibility_survey')
            .filter(
                profile__user_type='student',
                student_profile__isnull=False,
                is_staff=False,
                is_superuser=False,
            )
            .exclude(id=self.request.user.id)
            .exclude(profile__user_type='admin')
        )

        # Keep only users who have a completed survey and then apply hard filters.
        eligible = []
        for user in qs:
            survey = getattr(user, 'compatibility_survey', None)
            if not survey or not survey.is_completed():
                continue
            if filters['graduation_year'] and survey.graduation_year != filters['graduation_year']:
                continue
            if filters['major'] and survey.major != filters['major']:
                continue
            if filters['smoking_habits'] and survey.smoking_habits != filters['smoking_habits']:
                continue
            if filters['cleanliness']:
                clean_value = StudentCompatibilitySurvey.score_from_choice(survey.cleanliness)
                min_clean = StudentCompatibilitySurvey.score_from_choice(filters['cleanliness'])
                if clean_value is None or min_clean is None or clean_value < min_clean:
                    continue
            if filters['noise_level'] and survey.noise_level != filters['noise_level']:
                continue
            if filters['sleep_schedule']:
                candidate_sleep = StudentCompatibilitySurvey.score_from_choice(survey.sleep_schedule)
                viewer_sleep = StudentCompatibilitySurvey.score_from_choice(self.viewer_survey.sleep_schedule)
                if candidate_sleep is None or viewer_sleep is None:
                    continue
                if abs(
                    candidate_sleep - viewer_sleep
                ) > 1:
                    continue
            eligible.append(user)
        return eligible

    def _base_candidate_count(self):
        qs = (
            User.objects.select_related('compatibility_survey')
            .filter(
                profile__user_type='student',
                student_profile__isnull=False,
                is_staff=False,
                is_superuser=False,
            )
            .exclude(id=self.request.user.id)
            .exclude(profile__user_type='admin')
        )
        return sum(
            1
            for user in qs
            if getattr(user, 'compatibility_survey', None)
            and user.compatibility_survey.is_completed()
        )

    @staticmethod
    def _privacy_name(user):
        """Prefer StudentProfile names (onboarding) over auth User names; then username."""
        sp = getattr(user, 'student_profile', None)
        if sp:
            first_name = (sp.first_name or user.first_name or '').strip()
            last_name = (sp.last_name or user.last_name or '').strip()
        else:
            first_name = (user.first_name or '').strip()
            last_name = (user.last_name or '').strip()
        if first_name and last_name:
            return f'{first_name} {last_name[0]}.'
        if first_name:
            return first_name
        return user.username
