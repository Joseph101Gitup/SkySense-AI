"""
Test Suite 7: Image Upload Validation
Verifies:
- ImagePredictionForm validates image file presence
- Valid JPEG and PNG formats are accepted
- Missing image payload is rejected with field error
- File size exceeding MAX_UPLOAD_SIZE (15 MB) is rejected with clear validation error
- Web prediction interface (/predict/) validates uploads correctly
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from predictions.forms import ImagePredictionForm

User = get_user_model()


class ImageUploadValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='upload_tester', password='TestPassword123!')
        self.client.force_login(self.user)
        self.predict_url = reverse('predictions:predict')

    def test_form_accepts_valid_jpeg(self):
        """Verifies form is valid when provided with a proper JPEG."""
        img = Image.new('RGB', (256, 256), color=(50, 70, 90))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        file = SimpleUploadedFile('valid.jpg', img_io.getvalue(), content_type='image/jpeg')

        form = ImagePredictionForm(data={'notes': 'Test observation'}, files={'image': file})
        self.assertTrue(form.is_valid())

    def test_form_accepts_valid_png(self):
        """Verifies form is valid when provided with a proper PNG."""
        img = Image.new('RGB', (256, 256), color=(40, 80, 120))
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        file = SimpleUploadedFile('valid.png', img_io.getvalue(), content_type='image/png')

        form = ImagePredictionForm(data={}, files={'image': file})
        self.assertTrue(form.is_valid())

    def test_form_rejects_missing_image(self):
        """Verifies form is invalid when no image is uploaded."""
        form = ImagePredictionForm(data={'notes': 'No image attached'}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_form_rejects_oversized_file(self):
        """Verifies form rejects files larger than MAX_UPLOAD_SIZE (15 MB)."""
        img = Image.new('RGB', (100, 100), color=(100, 100, 100))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        file = SimpleUploadedFile('oversized.jpg', img_io.getvalue(), content_type='image/jpeg')
        file.size = settings.MAX_UPLOAD_SIZE + 1024

        form = ImagePredictionForm(data={}, files={'image': file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
        self.assertTrue(any('exceeds maximum allowed limit' in err for err in form.errors['image']))

    def test_predict_view_rejects_empty_post(self):
        """Verifies POST /predict/ without image returns form validation errors."""
        response = self.client.post(self.predict_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
