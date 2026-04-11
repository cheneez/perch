"""Resolve any user's public profile (student or lessor) for cross-app viewing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from accounts.models import Favorite, Profile
from lessor.models import LessorProfile
from student.models import HOBBY_TAG_OPTIONS, StudentProfile


def hobby_label_map():
    return dict(HOBBY_TAG_OPTIONS)


def _filled(val) -> bool:
    """True if a profile field should count as present (matches edit-form / live preview intent)."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (list, tuple, dict, set)):
        return len(val) > 0
    return bool(str(val).strip())


def _hobbies_list(p: StudentProfile) -> list:
    """JSONField should be a list; normalize bad legacy values so templates iterate safely."""
    raw = getattr(p, 'hobbies', None)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


@dataclass
class PublicProfileData:
    profile_user: User
    p: StudentProfile | LessorProfile
    profile_role: str  # 'student' | 'lessor'
    top_contacts: list[dict[str, Any]]
    sections: dict[str, Any]
    hobby_labels: dict[str, str]


def get_public_profile_url_for_user(user_or_id: int | User) -> str | None:
    """Canonical public profile URL for students/realtors; None for admins/staff or unknown users."""
    uid = user_or_id.pk if isinstance(user_or_id, User) else int(user_or_id)
    acc = Profile.objects.filter(user_id=uid).select_related('user').first()
    if not acc:
        return None
    user = acc.user
    if acc.user_type == 'admin' or user.is_staff or user.is_superuser:
        return None
    if acc.user_type == 'student':
        return reverse('student:public_profile', kwargs={'user_id': uid})
    if acc.user_type in ('realtor', 'lessor'):
        return reverse('lessor:public_profile', kwargs={'user_id': uid})
    return None


def resolve_public_profile(user_id: int) -> PublicProfileData:
    acc = Profile.objects.filter(user_id=user_id).select_related('user').first()
    if not acc:
        raise Http404()

    user = acc.user
    if acc.user_type == 'admin' or user.is_staff or user.is_superuser:
        raise Http404()

    if acc.user_type == 'student':
        p = get_object_or_404(StudentProfile.objects.select_related('user'), user_id=user_id)
        top = _top_contacts_public_student(p)
        sections = _section_flags_student(p)
        return PublicProfileData(
            profile_user=p.user,
            p=p,
            profile_role='student',
            top_contacts=top,
            sections=sections,
            hobby_labels=hobby_label_map(),
        )

    if acc.user_type in ('realtor', 'lessor'):
        p = get_object_or_404(LessorProfile.objects.select_related('user'), user_id=user_id)
        top = _top_contacts_public_lessor(p)
        sections = _section_flags_lessor(p)
        return PublicProfileData(
            profile_user=p.user,
            p=p,
            profile_role='lessor',
            top_contacts=top,
            sections=sections,
            hobby_labels={},
        )

    raise Http404()


def _top_contacts_public_student(profile: StudentProfile):
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


def _top_contacts_public_lessor(profile: LessorProfile):
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


def _section_flags_student(p: StudentProfile):
    about = any(
        _filled(x)
        for x in (
            p.display_name,
            p.bio,
            p.fun_fact_1,
            p.fun_fact_2,
            p.fun_fact_3,
        )
    )
    hobby_list = _hobbies_list(p)
    lifestyle = bool(hobby_list) or _filled(p.weekend_activities) or _filled(p.roommate_environment)
    # Align with edit_profile live preview: work block only if employment/role/budget text
    # or explicit "can contribute" yes — not unknown/no alone.
    work = (
        _filled(p.employment_status)
        or _filled(p.current_role)
        or _filled(p.housing_budget)
        or (p.can_contribute_rent is True)
    )
    social_any = False
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
            social_any = True
    return {
        'about': about,
        'lifestyle': lifestyle,
        'work': work,
        'social': social_any,
        'social_rows': social_rows,
        'hobby_list': hobby_list,
    }


def _section_flags_lessor(p: LessorProfile):
    about = any(
        _filled(x)
        for x in (
            p.display_name,
            p.bio,
            p.fun_fact_1,
            p.fun_fact_2,
            p.fun_fact_3,
        )
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
        'lifestyle': False,
        'work': False,
        'hobby_list': [],
        'social': bool(social_rows),
        'social_rows': social_rows,
    }


def toggle_public_profile_favorite(request: HttpRequest, user_id: int) -> HttpResponse:
    """POST-only: toggle Favorite for favorited_user=user_id; redirect to public profile."""
    app_name = request.resolver_match.app_name
    public_url = reverse(f'{app_name}:public_profile', kwargs={'user_id': user_id})
    self_profile_name = f'{app_name}:profile'

    if user_id == request.user.id:
        messages.error(request, 'You cannot add yourself to favorites.')
        return redirect(reverse(self_profile_name))

    resolve_public_profile(user_id)

    existing = Favorite.objects.filter(user=request.user, favorited_user_id=user_id).first()
    if existing:
        existing.delete()
    else:
        Favorite.objects.create(user=request.user, favorited_user_id=user_id)

    return redirect(public_url)
