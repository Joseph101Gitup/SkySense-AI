"""
Authentication & Authorization Test Suite for SKYsense AI.
Verifies:
- Registration using Django's built-in auth system with PBKDF2 password hashing
- Login with redirection to dashboard
- Logout functionality
- Password hashing validation (no custom password storage, no plaintext)
- Route protection with @login_required (redirects unauthenticated users)
- Prediction isolation: Regular users only see their own predictions
- Admin visibility: Staff / admin users can view and manage all predictions
- Permission denial (403 Forbidden) when non-admin accesses another user's prediction
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile

from predictions.models import Prediction, RainfallClass, SourceType

User = get_user_model()


class AuthenticationSystemTests(TestCase):
    """Tests for registration, login, logout, password hashing, and login_required guards."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')
        self.dashboard_url = reverse('core:dashboard')
        self.predict_url = reverse('predictions:predict')
        self.history_url = reverse('predictions:history')

    def test_user_registration_creates_hashed_password(self):
        """Verifies registration creates user with Django's native PBKDF2 password hashing."""
        response = self.client.post(self.register_url, {
            'username': 'researcher_eva',
            'email': 'eva@skysense.ai',
            'first_name': 'Eva',
            'last_name': 'Green',
            'password1': 'AtmosphericPass2026!',
            'password2': 'AtmosphericPass2026!',
        })
        # Successful registration redirects to LOGIN_REDIRECT_URL (dashboard)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

        user = User.objects.filter(username='researcher_eva').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'eva@skysense.ai')
        self.assertEqual(user.first_name, 'Eva')
        self.assertEqual(user.last_name, 'Green')

        # Critical: Password must NOT be plaintext
        self.assertNotEqual(user.password, 'AtmosphericPass2026!')
        # Must start with Django's default PBKDF2 algorithm prefix
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        # check_password must verify correctly
        self.assertTrue(check_password('AtmosphericPass2026!', user.password))

    def test_registration_validation_mismatched_passwords(self):
        """Verifies validation error on mismatched passwords."""
        response = self.client.post(self.register_url, {
            'username': 'mismatch_user',
            'email': 'mismatch@skysense.ai',
            'password1': 'SecretPassword123!',
            'password2': 'DifferentPassword456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password')
        self.assertFalse(User.objects.filter(username='mismatch_user').exists())

    def test_user_login_and_redirect_to_dashboard(self):
        """Verifies login with valid credentials redirects directly to dashboard."""
        User.objects.create_user(
            username='dr_watson',
            email='watson@skysense.ai',
            password='WatsonSecurePassword789!'
        )

        response = self.client.post(self.login_url, {
            'username': 'dr_watson',
            'password': 'WatsonSecurePassword789!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

    def test_user_login_invalid_credentials(self):
        """Verifies login failure on incorrect password."""
        User.objects.create_user(
            username='dr_watson',
            email='watson@skysense.ai',
            password='WatsonSecurePassword789!'
        )

        response = self.client.post(self.login_url, {
            'username': 'dr_watson',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_user_logout(self):
        """Verifies user logout terminates session and redirects."""
        user = User.objects.create_user(username='logout_tester', password='LogoutPassword123!')
        self.client.force_login(user)

        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        # Verify user is now unauthenticated
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unauthenticated_user_redirected_to_login(self):
        """Verifies protected views redirect anonymous users to /login/?next=..."""
        protected_routes = [
            (self.dashboard_url, '/login/?next=/dashboard/'),
            (self.predict_url, '/login/?next=/predict/'),
            (self.history_url, '/login/?next=/history/'),
            (self.profile_url, '/login/?next=/profile/'),
        ]

        for route, expected_redirect in protected_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, expected_redirect)

    def test_profile_view_displays_user_info(self):
        """Verifies profile page displays user metadata and activity."""
        user = User.objects.create_user(
            username='climate_researcher',
            email='climate@lab.org',
            first_name='Clara',
            last_name='Bow',
            password='ValidPassword123!'
        )
        self.client.force_login(user)

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'climate_researcher')
        self.assertContains(response, 'climate@lab.org')
        self.assertContains(response, 'Clara Bow')
        self.assertContains(response, 'Researcher')
        self.assertContains(response, 'PBKDF2 Password Hashed')


class UserIsolationAndPermissionTests(TestCase):
    """
    Tests ensuring strict prediction isolation between users
    and global visibility for administrator / staff accounts.
    """

    def setUp(self):
        self.client = Client()

        # Regular User A
        self.user_a = User.objects.create_user(
            username='alice_researcher',
            email='alice@lab.org',
            password='AlicePassword123!'
        )

        # Regular User B
        self.user_b = User.objects.create_user(
            username='bob_researcher',
            email='bob@lab.org',
            password='BobPassword123!'
        )

        # Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_director',
            email='admin@skysense.ai',
            password='AdminPassword123!'
        )

        # Sample image upload
        img = Image.new('RGB', (256, 256), color=(100, 150, 200))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        img_bytes = img_io.getvalue()

        # Prediction belonging to User A
        self.pred_a = Prediction.objects.create(
            user=self.user_a,
            image=SimpleUploadedFile('alice_cloud.jpg', img_bytes, content_type='image/jpeg'),
            original_filename='alice_cloud.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.82,
            low_to_medium_probability=0.82,
            medium_to_heavy_probability=0.10,
            no_to_low_probability=0.08,
            processing_time=95.0,
            source_type=SourceType.WEB_UPLOAD,
            user_notes='Alice observation'
        )

        # Prediction belonging to User B
        self.pred_b = Prediction.objects.create(
            user=self.user_b,
            image=SimpleUploadedFile('bob_cloud.jpg', img_bytes, content_type='image/jpeg'),
            original_filename='bob_cloud.jpg',
            predicted_class=RainfallClass.MEDIUM_TO_HEAVY,
            confidence=0.89,
            low_to_medium_probability=0.05,
            medium_to_heavy_probability=0.89,
            no_to_low_probability=0.06,
            processing_time=105.0,
            source_type=SourceType.WEB_UPLOAD,
            user_notes='Bob observation'
        )

    def test_user_only_sees_own_history(self):
        """Verifies User A only sees their own predictions in history."""
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alice_cloud.jpg')
        self.assertNotContains(response, 'bob_cloud.jpg')

        # Now login as User B
        self.client.force_login(self.user_b)
        response_b = self.client.get(reverse('predictions:history'))
        self.assertEqual(response_b.status_code, 200)
        self.assertContains(response_b, 'bob_cloud.jpg')
        self.assertNotContains(response_b, 'alice_cloud.jpg')

    def test_admin_sees_all_predictions_in_history(self):
        """Verifies administrator sees all predictions across the platform."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alice_cloud.jpg')
        self.assertContains(response, 'bob_cloud.jpg')

    def test_user_dashboard_scoped_to_own_predictions(self):
        """Verifies dashboard KPIs only count user's own predictions for non-admin."""
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_analyses'], 1)
        self.assertContains(response, 'alice_cloud.jpg')
        self.assertNotContains(response, 'bob_cloud.jpg')

        # API endpoint also scoped
        api_res = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data['total_analyses'], 1)
        self.assertEqual(data['most_recent']['original_filename'], 'alice_cloud.jpg')

    def test_admin_dashboard_sees_all_predictions(self):
        """Verifies admin dashboard includes all records in total count."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_analyses'], 2)

        api_res = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data['total_analyses'], 2)

    def test_permission_denied_when_accessing_other_users_prediction(self):
        """Verifies User A cannot view User B's prediction details (403 Forbidden)."""
        self.client.force_login(self.user_a)
        
        # User A tries to view User B's prediction detail
        response = self.client.get(reverse('predictions:detail', kwargs={'pk': self.pred_b.pk}))
        self.assertEqual(response.status_code, 403)

        # User A tries to view User B's result page
        res_result = self.client.get(reverse('predictions:result', kwargs={'pk': self.pred_b.pk}))
        self.assertEqual(res_result.status_code, 403)

        # User A tries to delete User B's prediction record
        res_delete = self.client.post(reverse('predictions:delete', kwargs={'pk': self.pred_b.pk}))
        self.assertEqual(res_delete.status_code, 403)
        # Ensure User B's record is still present in database
        self.assertTrue(Prediction.objects.filter(pk=self.pred_b.pk).exists())

    def test_admin_can_access_and_delete_any_prediction(self):
        """Verifies admin can access and delete predictions belonging to any user."""
        self.client.force_login(self.admin_user)

        # Admin accesses User A's detail
        res_detail = self.client.get(reverse('predictions:detail', kwargs={'pk': self.pred_a.pk}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'alice_cloud.jpg')

        # Admin deletes User A's prediction
        res_delete = self.client.post(reverse('predictions:delete', kwargs={'pk': self.pred_a.pk}))
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(Prediction.objects.filter(pk=self.pred_a.pk).exists())
