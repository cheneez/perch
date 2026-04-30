from django.contrib import messages
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Favorite, Profile
from chat.models import Conversation
from listings.models import Listing
from accounts.public_profile import (
    toggle_public_profile_favorite,
    try_resolve_public_profile,
)

from .forms import LessorCreateProfileForm, LessorEditDetailsForm, LessorEditProfileForm, VerificationRequestForm
from .models import LessorProfile, VerificationRequest


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
        user = self.request.user
        context['user'] = user
        context['my_listings'] = (
            Listing.objects.filter(
                owner=user,
                status=Listing.Status.AVAILABLE,
                moderation_status=Listing.ModerationStatus.APPROVED,
                is_hidden=False,
            )
            .prefetch_related('images')
            .order_by('-created_at')[:12]
        )
        context["pending_listings"] = (
            Listing.objects.filter(
                owner=user,
                moderation_status=Listing.ModerationStatus.PENDING,
            )
            .order_by('-created_at')[:5]
        )
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
            if conv.is_group:
                display_name = conv.name.strip() if conv.name else "Group chat"
            else:
                display_name = other.get_full_name() or other.username
            preview_items.append(
                {
                    "id": conv.id,
                    "other_name": display_name,
                    "last_snippet": last_msg.content[:80],
                    "timestamp": last_msg.created_at,
                }
            )
        context["recent_conversations"] = preview_items
        return context


class LessorMessagesView(LessorProfileRequiredMixin, RoleRequiredMixin, TemplateView):
    required_role = 'lessor'
    template_name = 'chat/messages.html'

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


class LessorVerificationView(LessorProfileRequiredMixin, RoleRequiredMixin, View):
    required_role = 'lessor'
    template_name = 'lessor/verification_status.html'

    def _get_profile_and_latest(self, request):
        profile = get_object_or_404(LessorProfile, user=request.user)
        latest = profile.verification_requests.order_by('-submitted_at').first()
        return profile, latest

    def get(self, request, *args, **kwargs):
        profile, latest = self._get_profile_and_latest(request)
        ctx = {
            'user': request.user,
            'p': profile,
            'latest': latest,
            'form': VerificationRequestForm(),
        }
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        profile, latest = self._get_profile_and_latest(request)

        # Block if already pending or verified
        if latest and latest.status == VerificationRequest.Status.PENDING:
            messages.warning(request, 'Your verification is already under review.')
            return redirect('lessor:verification')
        if latest and latest.status == VerificationRequest.Status.VERIFIED:
            messages.info(request, 'Your account is already verified.')
            return redirect('lessor:verification')

        form = VerificationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            VerificationRequest.objects.create(
                lessor=profile,
                government_id=form.cleaned_data['government_id'],
                property_proof=form.cleaned_data['property_proof'],
                status=VerificationRequest.Status.PENDING,
            )
            messages.success(request, 'Your documents have been submitted for review.')
            return redirect('lessor:verification')

        ctx = {
            'user': request.user,
            'p': profile,
            'latest': latest,
            'form': form,
        }
        return render(request, self.template_name, ctx)


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
        ctx['start_chat_url'] = f"{reverse('lessor:messages')}?start_chat={uid}"
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
