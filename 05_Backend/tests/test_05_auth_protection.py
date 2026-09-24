"""
Test Suite 5: Authentication Protection & Access Control
Verifies:
- Route protection with @login_required decorator:
  - /dashboard/
  - /predict/
  - /history/
  - /profile/
- Unauthenticated requests are redirected to /login/?next=<path>
- User data isolation: Regular users only see their own prediction records
- Cross-user security: Non-admin user gets 403 Forbidden when accessing another user's prediction
- Non-admin user gets 403 Forbidden when attempting to delete another user's prediction
- Staff/Admin permissions: Staff users can view and inspect all prediction records
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from predictions.models import Prediction, RainfallClass, SourceType

User = get_user_model()


class AuthenticationProtectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.dashboard_url = reverse('core:dashboard')
        self.predict_url = reverse('predictions:predict')
        self.history_url = reverse('predictions:history')
        self.profile_url = reverse('profile')

        # Users
        self.user_a = User.objects.create_user(username='user_alice', password='PasswordAlice123!')
        self.user_b = User.objects.create_user(username='user_bob', password='PasswordBob123!')
        self.admin_user = User.objects.create_superuser(username='admin_boss', password='AdminPassword123!', email='admin@skysense.ai')

        # Sample test image
        img = Image.new('RGB', (100, 100), color=(70, 90, 110))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        upload_a = SimpleUploadedFile('alice_cloud.jpg', img_io.getvalue(), content_type='image/jpeg')

        self.pred_alice = Prediction.objects.create(
            user=self.user_a,
            image=upload_a,
            original_filename='alice_cloud.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.82,
            low_to_medium_probability=0.82,
            medium_to_heavy_probability=0.10,
            no_to_low_probability=0.08,
            processing_time=120.0,
            source_type=SourceType.WEB_UPLOAD
        )

    def test_unauthenticated_routes_redirect_to_login(self):
        """Verifies unauthenticated requests to protected endpoints redirect to login."""
        protected_routes = [
            self.dashboard_url,
            self.predict_url,
            self.history_url,
            self.profile_url,
            reverse('predictions:detail', kwargs={'pk': self.pred_alice.pk}),
        ]

        for route in protected_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, f"Failed for route: {route}")
            self.assertIn(self.login_url, response.url)

    def test_authenticated_access_granted(self):
        """Verifies authenticated user can access protected endpoints."""
        self.client.force_login(self.user_a)

        self.assertEqual(self.client.get(self.dashboard_url).status_code, 200)
        self.assertEqual(self.client.get(self.predict_url).status_code, 200)
        self.assertEqual(self.client.get(self.history_url).status_code, 200)
        self.assertEqual(self.client.get(self.profile_url).status_code, 200)

    def test_prediction_history_user_isolation(self):
        """Verifies regular users only see their own prediction records."""
        # Alice sees her own prediction
        self.client.force_login(self.user_a)
        response_a = self.client.get(self.history_url)
        self.assertEqual(response_a.status_code, 200)
        self.assertContains(response_a, 'alice_cloud.jpg')

        # Bob does NOT see Alice's prediction
        self.client.force_login(self.user_b)
        response_b = self.client.get(self.history_url)
        self.assertEqual(response_b.status_code, 200)
        self.assertNotContains(response_b, 'alice_cloud.jpg')

    def test_cross_user_access_forbidden(self):
        """Verifies accessing another user's prediction returns 403 Forbidden."""
        self.client.force_login(self.user_b)
        detail_url = reverse('predictions:detail', kwargs={'pk': self.pred_alice.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 403)

    def test_cross_user_deletion_forbidden(self):
        """Verifies deleting another user's prediction returns 403 Forbidden."""
        self.client.force_login(self.user_b)
        delete_url = reverse('predictions:delete', kwargs={'pk': self.pred_alice.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Prediction.objects.filter(pk=self.pred_alice.pk).exists())

    def test_admin_can_access_any_prediction(self):
        """Verifies staff/admin users can view predictions owned by other users."""
        self.client.force_login(self.admin_user)
        detail_url = reverse('predictions:detail', kwargs={'pk': self.pred_alice.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alice_cloud.jpg')
