"""
Comprehensive Test Suite for SkySense AI Database Layer & Web Application.
Tests:
- Prediction model fields, defaults, and properties
- Database validation (probability summation, confidence limits, coordinates)
- Optional IoT telemetry fields and source_type constraints
- Django Admin interface viewability and custom badges
- Web presentation views & REST API endpoint
"""

import datetime
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from predictions.models import Prediction, SourceType, RainfallClass

User = get_user_model()


class SkySenseDatabaseModelTests(TestCase):
    """Specific tests verifying the Prediction database model and validation layer."""

    def setUp(self):
        img = Image.new('RGB', (256, 256), color=(60, 90, 120))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.test_upload = SimpleUploadedFile(
            name='db_test_cloud.jpg',
            content=img_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_prediction_creation_defaults(self):
        """Verifies default values, field assignment, and properties."""
        pred = Prediction.objects.create(
            image=self.test_upload,
            original_filename='db_test_cloud.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.745,
            low_to_medium_probability=0.745,
            medium_to_heavy_probability=0.155,
            no_to_low_probability=0.100,
            processing_time=124.5,
        )

        self.assertIsNotNone(pred.id)
        self.assertEqual(pred.source_type, SourceType.WEB_UPLOAD)
        self.assertEqual(pred.model_version, 'Xception-v1.0')
        self.assertEqual(pred.original_filename, 'db_test_cloud.jpg')
        self.assertEqual(pred.image_filename, 'db_test_cloud.jpg')
        self.assertEqual(pred.confidence_pct, 74.5)
        self.assertEqual(pred.prob_low_pct, 74.5)
        self.assertEqual(pred.prob_med_pct, 15.5)
        self.assertEqual(pred.prob_no_pct, 10.0)
        self.assertEqual(pred.latency_ms, 124.5)
        self.assertIsNone(pred.device_id)
        self.assertIsNone(pred.latitude)
        self.assertIsNone(pred.longitude)
        self.assertIsNone(pred.temperature)
        self.assertIsNone(pred.humidity)

    def test_optional_iot_fields_support(self):
        """Verifies optional edge IoT sensor fields can be stored when available."""
        pred = Prediction.objects.create(
            image=self.test_upload,
            original_filename='iot_station_node1.jpg',
            predicted_class=RainfallClass.MEDIUM_TO_HEAVY,
            confidence=0.880,
            low_to_medium_probability=0.080,
            medium_to_heavy_probability=0.880,
            no_to_low_probability=0.040,
            processing_time=98.2,
            source_type=SourceType.IOT_DEVICE,
            device_id='RPI4-SKY-NODE-07',
            latitude=12.9716,
            longitude=77.5946,
            temperature=24.5,
            humidity=82.0,
            user_notes='Edge station telemetry capture'
        )

        self.assertEqual(pred.source_type, SourceType.IOT_DEVICE)
        self.assertEqual(pred.device_id, 'RPI4-SKY-NODE-07')
        self.assertEqual(pred.latitude, 12.9716)
        self.assertEqual(pred.longitude, 77.5946)
        self.assertEqual(pred.temperature, 24.5)
        self.assertEqual(pred.humidity, 82.0)

    def test_database_validation_probability_sum(self):
        """Verifies clean() raises ValidationError if probabilities deviate significantly from 1.0."""
        pred = Prediction(
            image=self.test_upload,
            original_filename='invalid_prob.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.50,
            low_to_medium_probability=0.20,
            medium_to_heavy_probability=0.20,
            no_to_low_probability=0.20,  # Sum = 0.60 (Invalid)
            processing_time=50.0,
        )
        with self.assertRaises(ValidationError):
            pred.save()

    def test_database_validation_coordinate_pairing(self):
        """Verifies latitude without longitude raises ValidationError."""
        pred = Prediction(
            image=self.test_upload,
            original_filename='lone_coord.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.60,
            low_to_medium_probability=0.20,
            medium_to_heavy_probability=0.20,
            no_to_low_probability=0.60,
            processing_time=50.0,
            latitude=45.0,
            longitude=None  # Missing longitude
        )
        with self.assertRaises(ValidationError):
            pred.save()


class SkySenseAdminAndWebTests(TestCase):
    """Tests verifying Django Admin interface and Web prediction workflows."""

    def setUp(self):
        self.client = Client()
        # Create Superuser for Admin tests
        User = get_user_model()
        self.admin_user = User.objects.create_superuser('testadmin', 'testadmin@skysense.local', 'password123')
        
        # Test image
        img = Image.new('RGB', (256, 256), color=(73, 109, 137))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.test_image_bytes = img_io.getvalue()
        self.test_upload = SimpleUploadedFile(
            name='test_cloud.jpg',
            content=self.test_image_bytes,
            content_type='image/jpeg'
        )

    def test_admin_interface_access_and_rendering(self):
        """Verifies that Django Admin can view and inspect Prediction records."""
        pred = Prediction.objects.create(
            image=self.test_upload,
            original_filename='admin_sample.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.650,
            low_to_medium_probability=0.200,
            medium_to_heavy_probability=0.150,
            no_to_low_probability=0.650,
            processing_time=85.0,
        )

        self.client.force_login(self.admin_user)
        # Changelist view
        changelist_url = reverse('admin:predictions_prediction_changelist')
        response = self.client.get(changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin_sample.jpg')

        # Changeform / detail view
        changeform_url = reverse('admin:predictions_prediction_change', args=[pred.pk])
        response_detail = self.client.get(changeform_url)
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, 'Specimen &amp; Classification Result')
        self.assertContains(response_detail, 'Softmax Probability Distribution')

    def test_core_pages_render(self):
        """Test that all informational and analytics pages render with HTTP 200."""
        self.client.force_login(self.admin_user)
        routes = [
            'core:landing',
            'core:dashboard',
            'core:about',
            'core:model_info',
            'core:research_metrics',
            'accounts:profile',
            'predictions:predict',
            'predictions:history',
        ]
        for route_name in routes:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200, f"Route {route_name} failed with {response.status_code}")

    def test_ai_prediction_flow(self):
        """Test submitting an image through the web interface."""
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('predictions:predict'), {
            'image': self.test_upload,
            'notes': 'Automated integration test specimen'
        })
        self.assertEqual(response.status_code, 302)

        record = Prediction.objects.first()
        self.assertIsNotNone(record)
        self.assertEqual(record.source_type, SourceType.WEB_UPLOAD)
        self.assertIn(record.predicted_class, ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain'])
        self.assertGreater(record.confidence, 0.0)
        self.assertLessEqual(record.confidence, 1.0)

        # Test Result Page Requirements
        result_response = self.client.get(reverse('predictions:result', kwargs={'pk': record.pk}))
        self.assertEqual(result_response.status_code, 200)
        self.assertContains(result_response, record.display_name)
        self.assertContains(result_response, f"{record.confidence_percent}%")
        self.assertContains(result_response, "Low to Medium Rain")
        self.assertContains(result_response, "Medium to Heavy Rain")
        self.assertContains(result_response, "No to Low Rain")
        self.assertContains(result_response, record.model_version)
        self.assertContains(result_response, f"{record.latency_ms} ms")
        self.assertContains(result_response, "Analyze Another Image")
        self.assertContains(result_response, "View History")

        # Test Detail View GET & POST (update notes)
        detail_response = self.client.get(reverse('predictions:detail', kwargs={'pk': record.pk}))
        self.assertEqual(detail_response.status_code, 200)

        # Update Notes
        update_response = self.client.post(reverse('predictions:detail', kwargs={'pk': record.pk}), {
            'user_notes': 'Updated meteorological observations'
        })
        self.assertEqual(update_response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(record.user_notes, 'Updated meteorological observations')

        # History View
        history_response = self.client.get(reverse('predictions:history'))
        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, record.original_filename)

        # Delete View
        delete_response = self.client.post(reverse('predictions:delete', kwargs={'pk': record.pk}))
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(Prediction.objects.count(), 0)

    def test_error_handling_graceful(self):
        """Verifies invalid or corrupted files are handled gracefully without exposing tracebacks."""
        self.client.force_login(self.admin_user)
        # 1. Non-image file upload via Web form
        bad_file = SimpleUploadedFile('malicious.txt', b'NOT AN IMAGE', content_type='text/plain')
        response = self.client.post(reverse('predictions:predict'), {
            'image': bad_file,
            'notes': 'Should be rejected gracefully'
        })
        self.assertEqual(response.status_code, 200)  # Re-renders form with error flash message
        # Verify no traceback in response
        self.assertNotContains(response, 'Traceback (most recent call last)')
        self.assertContains(response, 'Upload a valid image')

        # 2. Corrupted file upload via API
        bad_api_file = SimpleUploadedFile('corrupt.jpg', b'INVALID BINARY DATA', content_type='image/jpeg')
        api_res = self.client.post(reverse('predictions:api_predict'), {'image': bad_api_file})
        self.assertEqual(api_res.status_code, 400)
        self.assertIn('error', api_res.json())
        self.assertNotIn('Traceback', str(api_res.content))

    def test_api_prediction_endpoint(self):
        """Test the REST API endpoint /api/predict/ with standard image upload."""
        img_upload = SimpleUploadedFile(
            name='api_test_cloud.jpg',
            content=self.test_image_bytes,
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('predictions:api_predict'), {
            'image': img_upload,
            'notes': 'API Integration Test'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Exact JSON format requested
        self.assertTrue(data.get('success'))
        self.assertIn(data.get('prediction'), ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain'])
        self.assertIsInstance(data.get('confidence'), float)
        self.assertGreater(data.get('confidence'), 0.0)
        
        probs = data.get('probabilities', {})
        self.assertIn('Low_to_Medium_Rain', probs)
        self.assertIn('Medium_to_Heavy_Rain', probs)
        self.assertIn('No_to_Low_Rain', probs)
        
        self.assertIsNotNone(data.get('timestamp'))
        self.assertEqual(data.get('model_version'), 'Xception-v1.0')

    def test_api_prediction_with_optional_iot_metadata(self):
        """Test /api/predict/ with optional future IoT metadata fields."""
        img_upload = SimpleUploadedFile(
            name='iot_sensor_cloud.jpg',
            content=self.test_image_bytes,
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('predictions:api_predict'), {
            'image': img_upload,
            'device_id': 'RPI4-SKY-NODE-01',
            'latitude': '12.9716',
            'longitude': '77.5946',
            'temperature': '26.4',
            'humidity': '68.5',
            'notes': 'Automated edge telemetry capture'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('device_id'), 'RPI4-SKY-NODE-01')
        self.assertEqual(data.get('latitude'), 12.9716)
        self.assertEqual(data.get('longitude'), 77.5946)
        self.assertEqual(data.get('temperature'), 26.4)
        self.assertEqual(data.get('humidity'), 68.5)
        self.assertEqual(data.get('source_type'), 'IOT_DEVICE')

        # Verify persisted in database
        record = Prediction.objects.get(id=data['id'])
        self.assertEqual(record.device_id, 'RPI4-SKY-NODE-01')
        self.assertEqual(record.latitude, 12.9716)
        self.assertEqual(record.longitude, 77.5946)
        self.assertEqual(record.temperature, 26.4)
        self.assertEqual(record.humidity, 68.5)
        self.assertEqual(record.source_type, 'IOT_DEVICE')

    def test_api_prediction_missing_image_parameter(self):
        """Test that calling /api/predict/ without an image returns 400 error."""
        response = self.client.post(reverse('predictions:api_predict'), {
            'device_id': 'ORPHAN-NODE-01'
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('image', data.get('error', '').lower())

    def test_api_prediction_invalid_coordinates(self):
        """Test that single coordinate or invalid float values return 400 error."""
        img_upload = SimpleUploadedFile(
            name='coord_test.jpg',
            content=self.test_image_bytes,
            content_type='image/jpeg'
        )
        # Latitude without longitude
        response = self.client.post(reverse('predictions:api_predict'), {
            'image': img_upload,
            'latitude': '12.9716'
        })
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('both latitude and longitude', data.get('error', '').lower())


class SkySensePredictionHistoryTests(TestCase):
    """
    Test suite for the /history/ archive view, detail view, filtering, sorting,
    pagination, and secure deletion.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='hist_researcher', password='HistPassword123!')
        self.client.force_login(self.user)

        img = Image.new('RGB', (256, 256), color=(50, 80, 110))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.img_bytes = img_io.getvalue()

        # Seed records with different classes, confidences, and source types
        self.pred1 = Prediction.objects.create(
            user=self.user,
            image=SimpleUploadedFile('cumulonimbus_heavy.jpg', self.img_bytes, content_type='image/jpeg'),
            original_filename='cumulonimbus_heavy.jpg',
            predicted_class=RainfallClass.MEDIUM_TO_HEAVY,
            confidence=0.92,
            low_to_medium_probability=0.05,
            medium_to_heavy_probability=0.92,
            no_to_low_probability=0.03,
            processing_time=95.0,
            model_version='Xception-v1.0',
            source_type=SourceType.WEB_UPLOAD,
            user_notes='Convective tower observed'
        )

        self.pred2 = Prediction.objects.create(
            user=self.user,
            image=SimpleUploadedFile('cirrus_dry.jpg', self.img_bytes, content_type='image/jpeg'),
            original_filename='cirrus_dry.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.68,
            low_to_medium_probability=0.20,
            medium_to_heavy_probability=0.12,
            no_to_low_probability=0.68,
            processing_time=110.0,
            model_version='Xception-v1.0',
            source_type=SourceType.IOT_DEVICE,
            device_id='NODE-TEST-01',
            user_notes='High thin wispy filaments'
        )

        self.pred3 = Prediction.objects.create(
            user=self.user,
            image=SimpleUploadedFile('stratocumulus_drizzle.jpg', self.img_bytes, content_type='image/jpeg'),
            original_filename='stratocumulus_drizzle.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.78,
            low_to_medium_probability=0.78,
            medium_to_heavy_probability=0.12,
            no_to_low_probability=0.10,
            processing_time=102.0,
            model_version='Xception-v1.0',
            source_type=SourceType.API,
            user_notes='Overcast low stratus base'
        )

    def test_history_list_view_renders(self):
        """Verifies that /history/ displays records, thumbnails, and badges."""
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cumulonimbus_heavy.jpg')
        self.assertContains(response, 'cirrus_dry.jpg')
        self.assertContains(response, 'stratocumulus_drizzle.jpg')
        self.assertContains(response, 'Prediction History')

    def test_history_search(self):
        """Tests search by filename, user notes, and UUID."""
        # Search by filename
        res_filename = self.client.get(reverse('predictions:history'), {'q': 'cumulonimbus'})
        self.assertEqual(res_filename.status_code, 200)
        self.assertContains(res_filename, 'cumulonimbus_heavy.jpg')
        self.assertNotContains(res_filename, 'cirrus_dry.jpg')

        # Search by notes
        res_notes = self.client.get(reverse('predictions:history'), {'q': 'wispy'})
        self.assertEqual(res_notes.status_code, 200)
        self.assertContains(res_notes, 'cirrus_dry.jpg')
        self.assertNotContains(res_notes, 'stratocumulus_drizzle.jpg')

        # Search by UUID
        res_uuid = self.client.get(reverse('predictions:history'), {'q': str(self.pred3.id)})
        self.assertEqual(res_uuid.status_code, 200)
        self.assertContains(res_uuid, 'stratocumulus_drizzle.jpg')
        self.assertNotContains(res_uuid, 'cirrus_dry.jpg')

    def test_history_category_filter(self):
        """Tests filtering by precipitation class."""
        response = self.client.get(reverse('predictions:history'), {'category': 'Medium_to_Heavy_Rain'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cumulonimbus_heavy.jpg')
        self.assertNotContains(response, 'cirrus_dry.jpg')
        self.assertNotContains(response, 'stratocumulus_drizzle.jpg')

    def test_history_date_filter(self):
        """Tests preset and custom date range filters."""
        # Preset today
        res_today = self.client.get(reverse('predictions:history'), {'date_range': 'today'})
        self.assertEqual(res_today.status_code, 200)
        self.assertEqual(len(res_today.context['page_obj']), 3)

        # Custom date range
        today_str = timezone.now().strftime('%Y-%m-%d')
        res_custom = self.client.get(reverse('predictions:history'), {'date_from': today_str, 'date_to': today_str})
        self.assertEqual(res_custom.status_code, 200)
        self.assertEqual(len(res_custom.context['page_obj']), 3)

    def test_history_sorting(self):
        """Tests ordering by newest, oldest, highest confidence, and lowest confidence."""
        # Highest confidence first
        res_conf = self.client.get(reverse('predictions:history'), {'sort': 'highest_confidence'})
        self.assertEqual(res_conf.status_code, 200)
        items = list(res_conf.context['page_obj'])
        self.assertEqual(items[0].original_filename, 'cumulonimbus_heavy.jpg')  # 0.92
        self.assertEqual(items[-1].original_filename, 'cirrus_dry.jpg')          # 0.68

        # Lowest confidence first
        res_low_conf = self.client.get(reverse('predictions:history'), {'sort': 'lowest_confidence'})
        items_low = list(res_low_conf.context['page_obj'])
        self.assertEqual(items_low[0].original_filename, 'cirrus_dry.jpg')      # 0.68

    def test_history_pagination(self):
        """Tests pagination splitting records 10 per page."""
        # Create 9 more records so total is 12
        for i in range(9):
            Prediction.objects.create(
                user=self.user,
                image=SimpleUploadedFile(f'cloud_{i}.jpg', self.img_bytes, content_type='image/jpeg'),
                original_filename=f'cloud_{i}.jpg',
                predicted_class=RainfallClass.NO_TO_LOW,
                confidence=0.70,
                low_to_medium_probability=0.15,
                medium_to_heavy_probability=0.15,
                no_to_low_probability=0.70,
                processing_time=100.0,
            )

        res_p1 = self.client.get(reverse('predictions:history'), {'page': '1'})
        self.assertEqual(res_p1.status_code, 200)
        self.assertEqual(len(res_p1.context['page_obj']), 10)
        self.assertTrue(res_p1.context['page_obj'].has_next())

        res_p2 = self.client.get(reverse('predictions:history'), {'page': '2'})
        self.assertEqual(res_p2.status_code, 200)
        self.assertEqual(len(res_p2.context['page_obj']), 2)

    def test_prediction_detail_displays_all_required_fields(self):
        """
        Verifies prediction detail page displays all mandatory specification elements:
        - uploaded image
        - prediction
        - confidence
        - probability distribution
        - timestamp
        - model version
        - processing time
        - source type
        - delete confirmation
        """
        response = self.client.get(reverse('predictions:detail', kwargs={'pk': self.pred1.pk}))
        self.assertEqual(response.status_code, 200)

        # 1. Uploaded image filename
        self.assertContains(response, 'cumulonimbus_heavy.jpg')
        # 2. Prediction display name
        self.assertContains(response, 'Medium to Heavy Rain')
        # 3. Confidence score
        self.assertContains(response, '92.0%')
        # 4. Probability distribution
        self.assertContains(response, 'Probability Distribution')
        self.assertContains(response, '92.0%')
        self.assertContains(response, '5.0%')
        self.assertContains(response, '3.0%')
        # 5. Timestamp
        self.assertContains(response, 'UTC')
        # 6. Model version
        self.assertContains(response, 'Xception-v1.0')
        # 7. Processing time
        self.assertContains(response, '95.0 ms')
        # 8. Source type
        self.assertContains(response, 'Web Upload')
        # 9. Delete functionality with confirmation
        self.assertContains(response, 'Delete Prediction Record')
        self.assertContains(response, 'confirm(')

    def test_safe_delete_record_and_file(self):
        """Tests that delete view rejects GET and deletes safely on POST."""
        # Reject GET
        get_res = self.client.get(reverse('predictions:delete', kwargs={'pk': self.pred1.pk}))
        self.assertEqual(get_res.status_code, 405)  # Method Not Allowed

        # Accept POST and delete
        post_res = self.client.post(reverse('predictions:delete', kwargs={'pk': self.pred1.pk}))
        self.assertEqual(post_res.status_code, 302)
        self.assertRedirects(post_res, reverse('predictions:history'))
        self.assertFalse(Prediction.objects.filter(pk=self.pred1.pk).exists())

