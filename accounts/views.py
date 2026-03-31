import json
from json import JSONDecodeError
import logging
import secrets
import urllib.error
import urllib.parse
import urllib.request
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse

from .models import Profile
from lessor.models import LessorProfile
from student.models import StudentProfile

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://openidconnect.googleapis.com/v1/userinfo'
logger = logging.getLogger(__name__)


def is_bc_email(email):
    return email.lower().endswith('@bc.edu')


def get_profile(user, default_role='student'):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'user_type': default_role},
    )
    return profile


def create_unique_username(email):
    base_username = email.split('@')[0]
    candidate = base_username
    suffix = 1

    while User.objects.filter(username=candidate).exclude(email__iexact=email).exists():
        candidate = f'{base_username}{suffix}'
        suffix += 1

    return candidate


def get_google_callback_url(request):
    configured_callback = settings.GOOGLE_OAUTH_CALLBACK_URL.strip()
    request_callback = request.build_absolute_uri(reverse('google_callback'))

    if configured_callback:
        configured_host = urllib.parse.urlparse(configured_callback).netloc
        if configured_host == request.get_host():
            return configured_callback

    return request_callback


def fetch_google_tokens(code, redirect_uri):
    payload = urllib.parse.urlencode(
        {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }
    ).encode('utf-8')
    request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=payload,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        raise ValueError(
            f'Google sign-in failed during token exchange: HTTP {exc.code} {error_body}'
        ) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, 'reason', exc)
        raise ValueError(
            f'Google sign-in failed during token exchange: network error ({reason}).'
        ) from exc
    except JSONDecodeError as exc:
        raise ValueError('Google sign-in failed during token exchange.') from exc


def fetch_google_userinfo(access_token):
    request = urllib.request.Request(
        GOOGLE_USERINFO_URL,
        headers={'Authorization': f'Bearer {access_token}'},
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        raise ValueError(
            f'Google sign-in failed while loading your profile: HTTP {exc.code} {error_body}'
        ) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, 'reason', exc)
        raise ValueError(
            f'Google sign-in failed while loading your profile: network error ({reason}).'
        ) from exc
    except JSONDecodeError as exc:
        raise ValueError('Google sign-in failed while loading your profile.') from exc


def oauth_is_configured():
    return bool(
        settings.GOOGLE_OAUTH_CLIENT_ID
        and settings.GOOGLE_OAUTH_CLIENT_SECRET
    )


def send_verification_email(request, user, profile):
    profile.email_verification_token = uuid.uuid4()
    profile.verification_email_sent_at = timezone.now()
    profile.save(update_fields=['email_verification_token', 'verification_email_sent_at'])
    token = profile.email_verification_token
    verify_url = request.build_absolute_uri(reverse('verify_confirm_short', args=[token]))
    subject = 'Verify your Perch account'
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        "Please verify your Perch account by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours."
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        messages.error(
            request,
            'We could not send the verification email right now. Check your email settings and try again.',
        )
        return False


def ensure_verified_or_redirect(request, profile):
    if profile.email_verified:
        return None
    return redirect('verify')


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email'].strip().lower()
        password = request.POST['password']
        try:
            user = User.objects.get(email__iexact=email)
            user = authenticate(username=user.username, password=password)
            if user:
                profile = get_profile(user)
                if profile.user_type == 'student':
                    messages.error(request, 'Students must sign in with Google using their @bc.edu email.')
                    return render(request, 'accounts/login.html', {'google_oauth_enabled': oauth_is_configured()})

                login(request, user)
                if not profile.email_verified:
                    return redirect('verify')
                return redirect('dashboard')

            messages.error(request, 'Wrong password')
        except User.DoesNotExist:
            if is_bc_email(email):
                messages.error(request, 'No local account found. BC students should sign in with Google.')
            else:
                messages.error(request, 'No account found')

    return render(
        request,
        'accounts/login.html',
        {'google_oauth_enabled': oauth_is_configured()},
    )


def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST['confirm_password']
        user_type = request.POST.get('user_type', 'student')

        if user_type not in dict(Profile.USER_TYPES):
            messages.error(request, 'Please choose a valid account type.')
            return render(request, 'accounts/signup.html', {'google_oauth_enabled': oauth_is_configured()})

        if user_type == 'student':
            # Students can only create accounts via their verified @bc.edu Google identity.
            # If a client submits a non-BC email here, block early (Google OAuth will also
            # enforce this again at callback time).
            if email and not is_bc_email(email):
                messages.error(request, 'Students must sign up with a verified @bc.edu email.')
                return render(
                    request,
                    'accounts/signup.html',
                    {'google_oauth_enabled': oauth_is_configured()},
                )
            return redirect(f"{reverse('google_start')}?role=student")

        if password != confirm_password:
            messages.error(request, '❌ Passwords do not match')
            return render(request, 'accounts/signup.html', {'google_oauth_enabled': oauth_is_configured()})

        if len(password) < 8:
            messages.error(request, '❌ Password must be at least 8 characters')
            return render(request, 'accounts/signup.html', {'google_oauth_enabled': oauth_is_configured()})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, '❌ An account with that email already exists')
            return render(request, 'accounts/signup.html', {'google_oauth_enabled': oauth_is_configured()})

        if not first_name or not last_name:
            messages.error(request, '❌ First and last name are required')
            return render(request, 'accounts/signup.html', {'google_oauth_enabled': oauth_is_configured()})

        username = create_unique_username(email)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        Profile.objects.create(user=user, user_type=user_type)
        profile = Profile.objects.get(user=user)
        login(request, user)
        send_verification_email(request, user, profile)
        return redirect('verify')

    return render(
        request,
        'accounts/signup.html',
        {'google_oauth_enabled': oauth_is_configured()},
    )


def google_start_view(request):
    if not oauth_is_configured():
        messages.error(
            request,
            'Google sign-in is not configured yet. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.',
        )
        return redirect('login')

    role = request.GET.get('role', 'student')
    if role != 'student':
        messages.error(request, 'Google sign-in is only available for BC student accounts.')
        return redirect('signup')

    state = secrets.token_urlsafe(32)
    redirect_uri = get_google_callback_url(request)
    request.session['google_oauth_state'] = state
    request.session['google_oauth_role'] = role
    request.session['google_oauth_redirect_uri'] = redirect_uri

    query = urllib.parse.urlencode(
        {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'prompt': 'select_account',
        }
    )
    return redirect(f'{GOOGLE_AUTH_URL}?{query}')


def google_callback_view(request):
    if request.GET.get('error'):
        messages.error(request, 'Google sign-in was cancelled.')
        return redirect('login')

    expected_state = request.session.pop('google_oauth_state', None)
    role = request.session.pop('google_oauth_role', 'student')
    redirect_uri = request.session.pop('google_oauth_redirect_uri', get_google_callback_url(request))
    returned_state = request.GET.get('state')
    code = request.GET.get('code')

    if not expected_state or returned_state != expected_state:
        messages.error(
            request,
            'Google sign-in failed because the browser session did not match. Use the same host for the full flow: either 127.0.0.1 everywhere or localhost everywhere.',
        )
        return redirect('login')

    if not code:
        messages.error(request, 'Google sign-in did not return an authorization code.')
        return redirect('login')

    try:
        token_data = fetch_google_tokens(code, redirect_uri)
        user_info = fetch_google_userinfo(token_data['access_token'])
    except (KeyError, ValueError) as exc:
        logger.warning('Google OAuth callback failed: %s', exc)
        messages.error(
            request,
            'Google sign-in could not be completed. Check the Google redirect URI and make sure your account is allowed as a test user.',
        )
        return redirect('login')

    email = user_info.get('email', '').strip().lower()
    email_verified = user_info.get('email_verified', False)

    if not email:
        messages.error(request, 'Google did not return an email address for this account.')
        return redirect('login')

    if role == 'student':
        if not email_verified:
            messages.error(request, 'Your Google account email must be verified to continue.')
            return redirect('login')
        if not is_bc_email(email):
            messages.error(request, 'Only @bc.edu Google accounts can sign in as students.')
            return redirect('login')

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.create_user(
            username=create_unique_username(email),
            email=email,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
        )
        user.set_unusable_password()
        user.save()
    else:
        updated_fields = []
        if not user.first_name and user_info.get('given_name'):
            user.first_name = user_info['given_name']
            updated_fields.append('first_name')
        if not user.last_name and user_info.get('family_name'):
            user.last_name = user_info['family_name']
            updated_fields.append('last_name')
        if updated_fields:
            user.save(update_fields=updated_fields)

    profile = get_profile(user, default_role=role)
    if profile.user_type != role:
        messages.error(
            request,
            'This email is already registered as a realtor account. Use email and password sign-in instead.',
        )
        return redirect('login')

    if role == 'student' and not profile.email_verified:
        # For BC student accounts created via Google OAuth, the Google `email_verified`
        # claim is our verification source of truth. Avoid forcing a separate email-link
        # verification step for student logins.
        profile.email_verified = True
        profile.email_verification_token = None
        profile.save(update_fields=['email_verified', 'email_verification_token'])

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    if not profile.email_verified:
        send_verification_email(request, user, profile)
        return redirect('verify')
    return redirect('dashboard')


def logout_view(request):
    logout(request)
    return redirect('/auth/login/')


def verify_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_profile(request.user)
    if profile.email_verified:
        return redirect('dashboard')

    return render(
        request,
        'accounts/verify.html',
        {
            'email': request.user.email,
            'user_type': profile.user_type,
        },
    )


def resend_verification_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_profile(request.user)
    if profile.email_verified:
        return redirect('dashboard')

    send_verification_email(request, request.user, profile)
    messages.success(request, 'We sent a new verification email.')
    return redirect('verify')


def verify_confirm_view(request, token):
    try:
        profile = Profile.objects.select_related('user').get(email_verification_token=token)
        user = profile.user
    except Profile.DoesNotExist:
        messages.error(request, 'That verification link is invalid or has expired.')
        return redirect('login')

    profile.email_verified = True
    profile.email_verification_token = None
    profile.save(update_fields=['email_verified', 'email_verification_token'])

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, 'Your email has been verified.')
    return redirect('dashboard')


def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_profile(request.user)
    redirect_response = ensure_verified_or_redirect(request, profile)
    if redirect_response is not None:
        return redirect_response
    if profile.user_type == 'student':
        if not StudentProfile.objects.filter(user=request.user).exists():
            return redirect(reverse('student:create_profile'))
        return redirect(reverse('student:dashboard'))
    if not LessorProfile.objects.filter(user=request.user).exists():
        return redirect(reverse('lessor:create_profile'))
    return redirect(reverse('lessor:dashboard'))
