"""
Test Suite 13: Unsupported File Format Handling
Verifies:
- Uploading forbidden or non-photographic file types is rejected by both:
  - The web form interface (/predict/)
  - The REST API endpoint (/api/predict/)
- File types tested:
  - Executables (.exe)
  - PDF documents (.pdf)
  - Plain text files (.txt)
  - Video clips (.mp4)
  - Compressed archives (.zip)
  - Vector graphics (.svg)
- Clean, actionable error messages are returned without exposing server internals.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()


class UnsupportedFileHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_url = reverse('predictions:api_predict')
        self.predict_url = reverse('predictions:predict')
        self.user = User.objects.create_user(username='file_format_tester', password='TestPassword123!')
        self.client.force_login(self.user)

    def test_api_rejects_executable_file(self):
        """Verifies API rejects .exe binaries with HTTP 400."""
        exe_file = SimpleUploadedFile(
            name='payload.exe',
            content=b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00',
            content_type='application/x-msdownload'
        )
        response = self.client.post(self.api_url, {'image': exe_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Unsupported file format', data['error'])

    def test_api_rejects_pdf_document(self):
        """Verifies API rejects PDF files with HTTP 400."""
        pdf_file = SimpleUploadedFile(
            name='document.pdf',
            content=b'%PDF-1.4\n%...\n%%EOF',
            content_type='application/pdf'
        )
        response = self.client.post(self.api_url, {'image': pdf_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Unsupported file format', data['error'])

    def test_api_rejects_text_document(self):
        """Verifies API rejects .txt files with HTTP 400."""
        txt_file = SimpleUploadedFile(
            name='notes.txt',
            content=b'Just some field notes.',
            content_type='text/plain'
        )
        response = self.client.post(self.api_url, {'image': txt_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Unsupported file format', data['error'])

    def test_api_rejects_mp4_video(self):
        """Verifies API rejects video files with HTTP 400."""
        mp4_file = SimpleUploadedFile(
            name='timelapse.mp4',
            content=b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00',
            content_type='video/mp4'
        )
        response = self.client.post(self.api_url, {'image': mp4_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Unsupported file format', data['error'])

    def test_web_form_rejects_unsupported_extensions(self):
        """Verifies web upload form rejects unsupported file formats with validation errors."""
        unsupported_files = [
            ('script.py', b'print("hello")', 'text/x-python'),
            ('data.zip', b'PK\x03\x04', 'application/zip'),
            ('vector.svg', b'<svg></svg>', 'image/svg+xml'),
        ]

        for filename, content, mime in unsupported_files:
            upload = SimpleUploadedFile(name=filename, content=content, content_type=mime)
            response = self.client.post(self.predict_url, {'image': upload})
            self.assertEqual(response.status_code, 200, f"Failed for {filename}")
            self.assertContains(
                response,
                'Upload a valid image',
                msg_prefix=f"Form should reject {filename}"
            )
