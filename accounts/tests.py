import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail

from lessor.models import LessorProfile

from .models import Profile


@override_settings(
    GOOGLE_OAUTH_CLIENT_ID='test-client-id',
    GOOGLE_OAUTH_CLIENT_SECRET='test-client-secret',
    GOOGLE_OAUTH_CALLBACK_URL='http://127.0.0.1:8000/auth/google/callback/',
    ALLOWED_HOSTS=['localhost', '127.0.0.1', 'testserver'],
)
class AuthFlowTests(TestCase):
    def test_realtor_signup_allows_non_bc_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'first_name': 'Casey',
                'last_name': 'Agent',
                'email': 'casey@realty.com',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
                'user_type': 'realtor',
            },
        )

        self.assertRedirects(response, reverse('verify'), fetch_redirect_response=False)
        user = User.objects.get(email='casey@realty.com')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user_type, 'realtor')
        self.assertEqual(len(mail.outbox), 1)

    def test_student_signup_redirects_to_google_flow(self):
        response = self.client.post(
            reverse('signup'),
            {
                'first_name': 'Jamie',
                'last_name': 'Student',
                'email': 'jamie@bc.edu',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
                'user_type': 'student',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f"{reverse('google_start')}?role=student")

    def test_student_signup_rejects_non_bc_email(self):
        response = self.client.post(
            reverse('signup'),
            {
                'first_name': 'Alex',
                'last_name': 'Student',
                'email': 'student@gmail.com',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
                'user_type': 'student',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Students must sign up with a verified @bc.edu email.')
        self.assertFalse(User.objects.filter(email='student@gmail.com').exists())

    def test_google_start_uses_request_host_when_callback_host_differs(self):
        response = self.client.get(
            reverse('google_start') + '?role=student',
            HTTP_HOST='localhost:8000',
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback%2F',
            response['Location'],
        )

    def test_local_login_blocks_student_accounts(self):
        user = User.objects.create_user(
            username='jamie',
            email='jamie@bc.edu',
            password='securepass123',
        )
        Profile.objects.create(user=user, user_type='student')

        response = self.client.post(
            reverse('login'),
            {'email': 'jamie@bc.edu', 'password': 'securepass123'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Students must sign in with Google')
        self.assertNotIn('_auth_user_id', self.client.session)

    @patch('accounts.views.fetch_google_userinfo')
    @patch('accounts.views.fetch_google_tokens')
    def test_google_callback_creates_bc_student_account(self, mock_fetch_tokens, mock_fetch_userinfo):
        mock_fetch_tokens.return_value = {'access_token': 'access-token'}
        mock_fetch_userinfo.return_value = {
            'email': 'eagle@bc.edu',
            'email_verified': True,
            'given_name': 'Eagle',
            'family_name': 'Student',
        }

        session = self.client.session
        session['google_oauth_state'] = 'expected-state'
        session['google_oauth_role'] = 'student'
        session.save()

        response = self.client.get(
            reverse('google_callback'),
            {'state': 'expected-state', 'code': 'oauth-code'},
        )

        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        user = User.objects.get(email='eagle@bc.edu')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user_type, 'student')
        self.assertTrue(profile.email_verified)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.id))
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_redirects_to_role_specific_page(self):
        user = User.objects.create_user(
            username='casey',
            email='casey@realty.com',
            password='securepass123',
            first_name='Casey',
            last_name='Agent',
        )
        Profile.objects.create(user=user, user_type='realtor', email_verified=True)
        LessorProfile.objects.create(
            user=user,
            username=user.username,
            first_name='Casey',
            last_name='Agent',
            gender_identity='prefer_not',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('lessor:dashboard'))

    def test_dashboard_redirects_unverified_user_to_verify_page(self):
        user = User.objects.create_user(
            username='jamie',
            email='jamie@bc.edu',
            password='securepass123',
        )
        Profile.objects.create(user=user, user_type='student', email_verified=False)
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('verify'))

    def test_verify_confirm_marks_user_verified(self):
        user = User.objects.create_user(
            username='verified',
            email='verified@bc.edu',
            password='securepass123',
        )
        profile = Profile.objects.create(user=user, user_type='student', email_verified=False)
        profile.email_verification_token = uuid.uuid4()
        profile.save(update_fields=['email_verification_token'])
        token = profile.email_verification_token

        response = self.client.get(reverse('verify_confirm', args=[token]))

        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        profile = Profile.objects.get(user=user)
        self.assertTrue(profile.email_verified)
        self.assertIsNone(profile.email_verification_token)

    @patch('accounts.views.fetch_google_userinfo')
    @patch('accounts.views.fetch_google_tokens')
    def test_google_callback_rejects_non_bc_student_account(self, mock_fetch_tokens, mock_fetch_userinfo):
        mock_fetch_tokens.return_value = {'access_token': 'access-token'}
        mock_fetch_userinfo.return_value = {
            'email': 'student@gmail.com',
            'email_verified': True,
            'given_name': 'Non',
            'family_name': 'BC',
        }

        session = self.client.session
        session['google_oauth_state'] = 'expected-state'
        session['google_oauth_role'] = 'student'
        session.save()

        response = self.client.get(
            reverse('google_callback'),
            {'state': 'expected-state', 'code': 'oauth-code'},
            follow=True,
        )

        self.assertContains(response, 'Only @bc.edu Google accounts can sign in as students.')
        self.assertFalse(User.objects.filter(email='student@gmail.com').exists())
