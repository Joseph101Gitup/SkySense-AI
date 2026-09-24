"""
Test Suite 14: Security Hardening & Vulnerability Verification
Checks and enforces:
- CSRF Protection
- XSS prevention (sanitized original_filename, HTML entity escaping)
- File upload validation (MIME types, size limits, deep binary verification)
- Path traversal protection (sample image path boundaries, safe media paths)
- Authorization and Access Control (cross-user isolation, unowned record protection)
- Safe randomized UUID storage paths for uploaded files
- Security headers (X-Content-Type-Options, X-Frame-Options)
"""

import os
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from predictions.models import Prediction, RainfallClass, SourceType, safe_prediction_image_path
from predictions.forms import ImagePredictionForm

User = get_user_model()


class SecurityHardeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.csrf_client = Client(enforce_csrf_checks=True)

        self.user_alice = User.objects.create_user(username='sec_alice', password='SecurePass123!')
        self.user_bob = User.objects.create_user(username='sec_bob', password='SecurePass456!')
        self.admin = User.objects.create_superuser(username='sec_admin', password='AdminPass789!', email='secadmin@skysense.ai')

        # Create valid synthetic JPEG image
        img = Image.new('RGB', (100, 100), color=(100, 140, 180))
        buf = BytesIO()
        img.save(buf, format='JPEG')
        self.valid_jpeg_bytes = buf.getvalue()

        # Create an unowned prediction (e.g. from IoT / system API)
        upload_iot = SimpleUploadedFile('iot_cloud.jpg', self.valid_jpeg_bytes, content_type='image/jpeg')
        self.unowned_prediction = Prediction.objects.create(
            user=None,
            image=upload_iot,
            original_filename='iot_cloud.jpg',
            predicted_class=RainfallClass.MEDIUM_TO_HEAVY,
            confidence=0.88,
            low_to_medium_probability=0.07,
            medium_to_heavy_probability=0.88,
            no_to_low_probability=0.05,
            processing_time=95.0,
            source_type=SourceType.IOT_DEVICE
        )

    def test_path_traversal_sample_image_rejected(self):
        """Verifies predict_sample_view rejects path traversal payloads like ../../etc/passwd."""
        self.client.force_login(self.user_alice)
        traversal_payloads = [
            '../../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\cmd.exe',
            'C:\\Windows\\System32\\drivers\\etc\\hosts',
            'd:\\personal\\SkySense_AI\\05_Backend\\manage.py',
        ]
        url = reverse('predictions:predict_sample')
        for payload in traversal_payloads:
            response = self.client.post(url, {'sample_path': payload}, follow=True)
            # Must redirect back to predict page with error, never attempt to execute/read
            self.assertEqual(response.status_code, 200)
            messages = [m.message for m in response.context['messages']]
            self.assertTrue(
                any('Invalid sample image path' in m or 'does not exist' in m for m in messages),
                f"Failed to reject traversal payload: {payload}"
            )

    def test_unauthorized_access_to_unowned_prediction(self):
        """Verifies regular users receive 403 Forbidden when accessing unowned prediction records."""
        self.client.force_login(self.user_bob)

        # Attempt to access result view of unowned prediction
        result_url = reverse('predictions:result', kwargs={'pk': self.unowned_prediction.pk})
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, 403, "Non-admin user should not access unowned prediction result")

        # Attempt to access detail view of unowned prediction
        detail_url = reverse('predictions:detail', kwargs={'pk': self.unowned_prediction.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 403, "Non-admin user should not access unowned prediction detail")

        # Admin user should be allowed
        self.client.force_login(self.admin)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

    def test_filename_sanitization_removes_dangerous_characters(self):
        """Verifies original_filename strips path traversal, XSS tags, and null bytes upon model save."""
        dangerous_names = [
            '../../evil_payload.jpg',
            '<script>alert("XSS")</script>.png',
            'cloud\x00_test.jpeg',
            '../../../windows/system32/cmd.exe',
            'safe_photo.jpg',
        ]
        for malicious_name in dangerous_names:
            upload = SimpleUploadedFile(malicious_name, self.valid_jpeg_bytes, content_type='image/jpeg')
            pred = Prediction(
                user=self.user_alice,
                image=upload,
                original_filename=malicious_name,
                predicted_class=RainfallClass.NO_TO_LOW,
                confidence=0.91,
                low_to_medium_probability=0.04,
                medium_to_heavy_probability=0.05,
                no_to_low_probability=0.91,
                processing_time=80.0
            )
            pred.save()
            self.assertNotIn('<', pred.original_filename)
            self.assertNotIn('>', pred.original_filename)
            self.assertNotIn('/', pred.original_filename)
            self.assertNotIn('\\', pred.original_filename)
            self.assertNotIn('\x00', pred.original_filename)

    def test_safe_prediction_image_path_generates_random_uuid_filename(self):
        """Verifies safe_prediction_image_path stores files with randomized UUIDs to prevent collisions/traversals."""
        path = safe_prediction_image_path(None, 'arbitrary_name.png')
        self.assertTrue(path.startswith('predictions/'))
        self.assertTrue(path.endswith('.png'))
        filename = os.path.basename(path)
        # Should be a 32-char hex UUID + .png
        raw_uuid = os.path.splitext(filename)[0]
        self.assertEqual(len(raw_uuid), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in raw_uuid))

    def test_oversized_upload_rejection_in_form(self):
        """Verifies upload form rejects files larger than MAX_UPLOAD_SIZE (15 MB)."""
        upload = SimpleUploadedFile('oversized.jpg', self.valid_jpeg_bytes, content_type='image/jpeg')
        upload.size = settings.MAX_UPLOAD_SIZE + 1024  # Force size property above limit
        form = ImagePredictionForm(data={}, files={'image': upload})
        self.assertFalse(form.is_valid())
        self.assertTrue(any('exceeds maximum allowed limit' in err for err in form.errors.get('image', [])))

    def test_oversized_upload_rejection_in_api(self):
        """Verifies API rejects payloads larger than MAX_UPLOAD_SIZE with HTTP 400."""
        oversized_bytes = b'0' * (settings.MAX_UPLOAD_SIZE + 1024)
        upload = SimpleUploadedFile('oversized.jpg', oversized_bytes, content_type='image/jpeg')
        response = self.client.post('/api/predict/', {'image': upload})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('limit', data['error'].lower())

    def test_mime_type_validation_rejects_unallowed_types(self):
        """Verifies API rejects unallowed MIME types with HTTP 400."""
        unallowed_types = ['image/svg+xml', 'application/pdf', 'text/html', 'video/mp4']
        for mime in unallowed_types:
            upload_api = SimpleUploadedFile('test.jpg', self.valid_jpeg_bytes, content_type=mime)
            response = self.client.post('/api/predict/', {'image': upload_api})
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('mime', data['error'].lower())

    def test_form_rejects_unsupported_image_types(self):
        """Verifies form rejects formats other than JPEG and PNG (e.g. GIF)."""
        gif_buf = BytesIO()
        Image.new('RGB', (50, 50)).save(gif_buf, format='GIF')
        upload = SimpleUploadedFile('sample.gif', gif_buf.getvalue(), content_type='image/gif')
        form = ImagePredictionForm(data={}, files={'image': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_security_headers_present(self):
        """Verifies critical defensive HTTP security headers are set in HTTP responses."""
        response = self.client.get(reverse('core:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')

    def test_csrf_protection_enforced_on_web_post(self):
        """Verifies CSRF verification blocks POST requests missing valid CSRF tokens on web endpoints."""
        self.csrf_client.force_login(self.user_alice)
        # Attempt POST to predict without valid CSRF
        response = self.csrf_client.post(reverse('predictions:predict'), {'notes': 'test'})
        self.assertEqual(response.status_code, 403, "POST without CSRF token should return 403 Forbidden")
