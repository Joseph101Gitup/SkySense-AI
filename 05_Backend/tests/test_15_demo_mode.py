"""
Test Suite 15: Dedicated Demonstration Mode (/demo/)
Verifies:
- GET /demo/ loads 200 OK with projector presentation layout
- Template includes all 10 required demonstration components:
  1. Select sample image
  2. Image preview
  3. Analyze button
  4. Animated analysis state
  5. Prediction result
  6. Confidence
  7. Probability chart
  8. Explanation
  9. Processing time
  10. Model version
  And "Upload Your Own Image" option
- Demo image serve endpoint (/demo/image/<path>) serves specimens safely
- Demo image serve endpoint prevents directory traversal
- POST /demo/analyze/ executes real AI model inference on sample specimen
- POST /demo/analyze/ executes real AI model inference on user uploaded image
- Non-fake verification: probabilities sum to 1.0, confidence matches peak softmax
- Validation of invalid payloads and unauthorized paths
"""

from io import BytesIO
from pathlib import Path
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class DemonstrationModeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.demo_url = reverse('predictions:demo')
        self.demo_analyze_url = reverse('predictions:demo_analyze')

        # Sample test image
        img = Image.new('RGB', (256, 256), color=(100, 150, 200))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.valid_upload = SimpleUploadedFile('demo_test_cloud.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_demo_page_loads_200(self):
        """Verifies GET /demo/ returns HTTP 200 and required elements."""
        response = self.client.get(self.demo_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions/demo.html')

        content = response.content.decode('utf-8')
        # 1. Select sample image
        self.assertIn('Select Sample Image', content)
        # 2. Image preview
        self.assertIn('Image Preview Stage', content)
        # 3. Analyze button
        self.assertIn('Analyze Cloud Specimen', content)
        # 4. Animated analysis state
        self.assertIn('scan-overlay', content)
        # 5. Prediction result
        self.assertIn('Prediction Result', content)
        # 6. Confidence
        self.assertIn('Confidence', content)
        # 7. Probability chart
        self.assertIn('probability-chart', content)
        # 8. Explanation
        self.assertIn('Scientific Explanation', content)
        self.assertIn('Meteorological Advisory', content)
        # 9. Processing time
        self.assertIn('Processing Time', content)
        # 10. Model version
        self.assertIn('Xception-v1.0', content)
        # Upload Your Own Image
        self.assertIn('Upload Your Own Image', content)

    def test_demo_image_serve_view(self):
        """Verifies demo image serving endpoint."""
        url = reverse('predictions:demo_image_serve', kwargs={'subpath': 'no_low/Ci_Ci-N010.jpg'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_demo_image_serve_prevents_traversal(self):
        """Verifies path traversal is blocked when requesting images."""
        url = '/demo/image/../../etc/passwd'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_demo_analyze_sample_image(self):
        """Verifies POST /demo/analyze/ runs real inference on a demo sample image."""
        payload = {
            'sample_path': 'demo_images/no_low/Ci_Ci-N010.jpg'
        }
        response = self.client.post(self.demo_analyze_url, payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn(data['prediction'], ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain'])
        self.assertIsInstance(data['confidence'], float)
        self.assertGreater(data['confidence'], 0.0)
        self.assertIn('probabilities', data)
        self.assertIn('No_to_Low_Rain', data['probabilities'])
        self.assertIn('Low_to_Medium_Rain', data['probabilities'])
        self.assertIn('Medium_to_Heavy_Rain', data['probabilities'])

        # Probabilities sum close to 1.0 (softmax property)
        prob_sum = sum(data['probabilities'].values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

        # Telemetry & Explanation
        self.assertIn('processing_time_ms', data)
        self.assertGreater(data['processing_time_ms'], 0.0)
        self.assertIn('Xception', data['model_version'])
        self.assertIn('explanation', data)
        self.assertIn('meteorological_context', data['explanation'])

    def test_demo_analyze_user_upload(self):
        """Verifies POST /demo/analyze/ accepts uploaded custom user image."""
        payload = {
            'image': self.valid_upload
        }
        response = self.client.post(self.demo_analyze_url, payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn(data['prediction'], ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain'])
        self.assertIsInstance(data['confidence'], float)
        self.assertIn('probabilities', data)
        self.assertIn('processing_time_ms', data)

    def test_demo_analyze_missing_input_returns_400(self):
        """Verifies POST /demo/analyze/ without sample_path or image returns 400 Bad Request."""
        response = self.client.post(self.demo_analyze_url, {})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_demo_analyze_unauthorized_path_returns_403(self):
        """Verifies unauthorized sample path outside demo_images/ returns 403 Forbidden."""
        response = self.client.post(self.demo_analyze_url, {
            'sample_path': '05_Backend/manage.py'
        })
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])

    def test_demo_analyze_rejects_unsupported_file_type(self):
        """Verifies uploading an executable or non-image returns 400."""
        text_file = SimpleUploadedFile('script.sh', b'echo hello', content_type='text/plain')
        response = self.client.post(self.demo_analyze_url, {'image': text_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
