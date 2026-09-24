"""
Test Suite 4: User Registration
Verifies:
- GET /register/ renders registration form
- POST /register/ creates new User instance in database
- Registration automatically hashes password with Django's native PBKDF2 algorithm
- Critical Security: Plaintext password is NEVER stored in database
- Successful registration logs user in and redirects to dashboard
- Password confirmation mismatch is detected and rejected
- Duplicate username collision is detected and rejected
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.dashboard_url = reverse('core:dashboard')

    def test_register_page_renders_form(self):
        """Verifies GET /register/ returns 200 OK and presents registration fields."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Researcher Account')
        self.assertContains(response, 'username')
        self.assertContains(response, 'email')
        self.assertContains(response, 'password1')
        self.assertContains(response, 'password2')

    def test_registration_success_hashes_password_and_redirects(self):
        """Verifies registration creates user with PBKDF2 hashing and redirects to dashboard."""
        raw_password = 'AtmosphericPass2026!'
        response = self.client.post(self.register_url, {
            'username': 'new_meteorologist',
            'email': 'meteo@skysense.ai',
            'first_name': 'Alan',
            'last_name': 'Turing',
            'password1': raw_password,
            'password2': raw_password,
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

        user = User.objects.filter(username='new_meteorologist').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'meteo@skysense.ai')
        self.assertEqual(user.first_name, 'Alan')
        self.assertEqual(user.last_name, 'Turing')

        # Critical: Password must NOT be plaintext
        self.assertNotEqual(user.password, raw_password)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(check_password(raw_password, user.password))

        # Verify user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_validation_mismatched_passwords(self):
        """Verifies registration fails when password and confirmation do not match."""
        response = self.client.post(self.register_url, {
            'username': 'mismatched_user',
            'email': 'mismatch@skysense.ai',
            'password1': 'FirstPassword123!',
            'password2': 'SecondPassword456!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'match' in str(response.content).lower() or
            'password' in str(response.context['form'].errors).lower()
        )
        self.assertFalse(User.objects.filter(username='mismatched_user').exists())

    def test_registration_duplicate_username_rejected(self):
        """Verifies registration fails when requested username is already taken."""
        User.objects.create_user(
            username='existing_user',
            email='existing@skysense.ai',
            password='InitialPassword123!'
        )

        response = self.client.post(self.register_url, {
            'username': 'existing_user',
            'email': 'different_email@skysense.ai',
            'password1': 'AnotherPassword123!',
            'password2': 'AnotherPassword123!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
        self.assertEqual(User.objects.filter(username='existing_user').count(), 1)
