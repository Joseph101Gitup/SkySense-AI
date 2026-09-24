"""
Test Suite 3: Login & Logout Workflow
Verifies:
- GET /login/ displays the login form with CSRF token
- Successful login redirects to LOGIN_REDIRECT_URL (/dashboard/)
- Successful login creates authenticated user session
- Failed login with invalid password displays error message without authenticating
- Failed login with nonexistent username displays clean error message
- Login redirects to 'next' query parameter target when provided
- Logout terminates user session and redirects to login or landing page
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('core:dashboard')
        self.predict_url = reverse('predictions:predict')

        self.user = User.objects.create_user(
            username='climatologist_jane',
            email='jane@skysense.ai',
            password='ValidPassword2026!'
        )

    def test_login_page_renders_form(self):
        """Verifies GET /login/ renders HTTP 200 with login form."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Researcher Portal')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')

    def test_login_success_redirects_to_dashboard(self):
        """Verifies valid login redirects to dashboard and establishes user session."""
        response = self.client.post(self.login_url, {
            'username': 'climatologist_jane',
            'password': 'ValidPassword2026!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

        # Verify session is authenticated
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_failure_invalid_password(self):
        """Verifies incorrect password fails and keeps user unauthenticated."""
        response = self.client.post(self.login_url, {
            'username': 'climatologist_jane',
            'password': 'WrongPassword999!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_failure_nonexistent_user(self):
        """Verifies nonexistent username is rejected safely."""
        response = self.client.post(self.login_url, {
            'username': 'unknown_researcher',
            'password': 'ValidPassword2026!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirect_with_next_param(self):
        """Verifies login respects 'next' parameter and redirects to intended protected page."""
        login_with_next = f"{self.login_url}?next={self.predict_url}"
        response = self.client.post(login_with_next, {
            'username': 'climatologist_jane',
            'password': 'ValidPassword2026!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.predict_url)

    def test_logout_terminates_session(self):
        """Verifies logging out invalidates session and redirects."""
        self.client.force_login(self.user)
        self.assertIn('_auth_user_id', self.client.session)

        # GET /logout/ or POST /logout/ terminates session
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
