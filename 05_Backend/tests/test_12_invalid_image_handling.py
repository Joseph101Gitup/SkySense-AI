"""
Test Suite 12: Invalid & Corrupted Image Handling
Verifies:
- Uploading non-image data disguised as .jpg (e.g. plain text or random binary bytes)
  is safely rejected by both the web interface and the REST API.
- Zero-byte (empty) files are detected and rejected with 400 Bad Request.
- Truncated or corrupted image streams do not cause unhandled 500 exceptions or leak stack traces.
- Direct invocation of RainfallInferenceService raises CorruptedImageError on bad input.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from predictions.services import (
    RainfallInferenceService,
    CorruptedImageError,
    InferenceError
)

User = get_user_model()


class InvalidImageHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_url = reverse('predictions:api_predict')
        self.predict_url = reverse('predictions:predict')
        self.user = User.objects.create_user(username='corrupt_tester', password='TestPassword123!')
        self.client.force_login(self.user)

    def test_api_rejects_plain_text_renamed_as_jpg(self):
        """Verifies API rejects text files renamed as .jpg with HTTP 400 (not 500)."""
        fake_jpg = SimpleUploadedFile(
            name='fake_cloud.jpg',
            content=b'This is not a real JPEG image file. It is plain ASCII text.',
            content_type='image/jpeg'
        )
        response = self.client.post(self.api_url, {'image': fake_jpg})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertTrue(
            'decode' in data['error'].lower() or
            'corrupt' in data['error'].lower() or
            'image' in data['error'].lower()
        )

    def test_api_rejects_empty_zero_byte_file(self):
        """Verifies API rejects 0-byte file payload with HTTP 400."""
        empty_jpg = SimpleUploadedFile(
            name='empty.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        response = self.client.post(self.api_url, {'image': empty_jpg})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_api_rejects_corrupted_truncated_jpeg(self):
        """Verifies API handles truncated JPEG headers safely without internal server error."""
        # Valid JPEG start marker 0xFF 0xD8 followed by corrupted garbage
        truncated_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00' + b'\x00' * 50
        truncated_jpg = SimpleUploadedFile(
            name='truncated.jpg',
            content=truncated_bytes,
            content_type='image/jpeg'
        )
        response = self.client.post(self.api_url, {'image': truncated_jpg})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_web_form_rejects_fake_image(self):
        """Verifies web upload form detects and displays validation error for non-image."""
        fake_jpg = SimpleUploadedFile(
            name='fake_cloud.jpg',
            content=b'Not an image payload.',
            content_type='image/jpeg'
        )
        response = self.client.post(self.predict_url, {'image': fake_jpg})
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertContains(response, 'Upload a valid image')

    def test_inference_service_raises_on_invalid_bytes(self):
        """Verifies service layer raises CorruptedImageError directly when fed invalid bytes."""
        service = RainfallInferenceService.get_instance()
        with self.assertRaises(CorruptedImageError):
            service.predict(b'Random invalid bytes that cannot be decoded as image')
