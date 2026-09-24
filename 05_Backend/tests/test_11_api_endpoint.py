"""
Test Suite 11: REST API Endpoint (POST /api/predict/)
Verifies:
- POST /api/predict/ accepts multipart/form-data containing 'image'
- Returns structured JSON response conforming to API documentation specification:
  - success: true
  - prediction: string
  - confidence: float
  - probabilities: dict with Low_to_Medium_Rain, Medium_to_Heavy_Rain, No_to_Low_Rain
  - timestamp: ISO-8601 string
  - model_version: string
- Optional IoT telemetry ingestion (device_id, latitude, longitude, temperature, humidity)
- Endpoint is @csrf_exempt (accessible to headless / edge IoT nodes without CSRF token)
- Missing required 'image' parameter returns 400 Bad Request
- HTTP GET returns 405 Method Not Allowed
- Coordinate completeness validation (latitude without longitude returns 400)
- Environmental reading validation (out-of-range humidity returns 400)
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class ApiEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_url = reverse('predictions:api_predict')

        img = Image.new('RGB', (256, 256), color=(75, 95, 115))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.valid_upload = SimpleUploadedFile('api_cloud.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_api_predict_success(self):
        """Verifies POST /api/predict/ returns 200 OK and expected JSON structure."""
        response = self.client.post(self.api_url, {'image': self.valid_upload})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn(data['prediction'], ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain'])
        self.assertIsInstance(data['confidence'], float)
        self.assertIn('probabilities', data)
        self.assertIn('Low_to_Medium_Rain', data['probabilities'])
        self.assertIn('Medium_to_Heavy_Rain', data['probabilities'])
        self.assertIn('No_to_Low_Rain', data['probabilities'])
        self.assertIsNotNone(data['timestamp'])
        self.assertEqual(data['model_version'], 'Xception-v1.0')
        self.assertIn('id', data)
        self.assertIn('processing_time_ms', data)

    def test_api_predict_with_iot_metadata(self):
        """Verifies optional IoT metadata is accepted, stored, and echoed in response."""
        img = Image.new('RGB', (256, 256), color=(85, 105, 125))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        upload = SimpleUploadedFile('iot_node_test.jpg', img_io.getvalue(), content_type='image/jpeg')

        response = self.client.post(self.api_url, {
            'image': upload,
            'device_id': 'TEST-ESP32-NODE-01',
            'latitude': '12.9716',
            'longitude': '77.5946',
            'temperature': '25.5',
            'humidity': '78.0',
            'notes': 'Automated IoT Station Ingestion'
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['source_type'], 'IOT_DEVICE')
        self.assertEqual(data['device_id'], 'TEST-ESP32-NODE-01')
        self.assertEqual(data['latitude'], 12.9716)
        self.assertEqual(data['longitude'], 77.5946)
        self.assertEqual(data['temperature'], 25.5)
        self.assertEqual(data['humidity'], 78.0)

    def test_api_missing_image_parameter(self):
        """Verifies 400 Bad Request when 'image' parameter is absent."""
        response = self.client.post(self.api_url, {'notes': 'No image sent'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Missing required parameter', data['error'])

    def test_api_method_not_allowed_for_get(self):
        """Verifies GET request to /api/predict/ returns 405 Method Not Allowed."""
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 405)

    def test_api_unpaired_coordinates_rejected(self):
        """Verifies supplying latitude without longitude returns 400 Bad Request."""
        img = Image.new('RGB', (100, 100), color=(50, 50, 50))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        upload = SimpleUploadedFile('unpaired.jpg', img_io.getvalue(), content_type='image/jpeg')

        response = self.client.post(self.api_url, {
            'image': upload,
            'latitude': '12.9716'  # Missing longitude
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Both latitude and longitude must be provided together', data['error'])

    def test_api_invalid_humidity_rejected(self):
        """Verifies out-of-range humidity (> 100%) returns 400 Bad Request."""
        img = Image.new('RGB', (100, 100), color=(50, 50, 50))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        upload = SimpleUploadedFile('invalid_hum.jpg', img_io.getvalue(), content_type='image/jpeg')

        response = self.client.post(self.api_url, {
            'image': upload,
            'humidity': '150.0'
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Humidity must be a percentage between 0.0 and 100.0', data['error'])
