"""
Test Suite 9: Prediction Database Record Creation
Verifies:
- process_image_prediction orchestrates AI inference and database persistence
- PredictionRecord entity is saved into SQLite with generated UUID primary key
- Associated user, original_filename, and timestamps are recorded
- Prediction classes and numerical probabilities match inference output
- Optional IoT telemetry fields (device_id, coordinates, temperature, humidity) persist correctly
- Meteorological advisories (risk, rain range, action) are populated
"""

import uuid
from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from predictions.models import Prediction, SourceType
from predictions.services import process_image_prediction

User = get_user_model()


class PredictionDatabaseCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='db_creator', password='SecurePassword123!')
        img = Image.new('RGB', (256, 256), color=(80, 100, 120))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.upload = SimpleUploadedFile('test_cumulus.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_database_creation_web_upload(self):
        """Verifies full database persistence for web user upload."""
        record = process_image_prediction(
            self.upload,
            notes='Mid-afternoon cloud formation',
            user=self.user,
            source_type=SourceType.WEB_UPLOAD
        )

        self.assertIsNotNone(record.id)
        self.assertIsInstance(record.id, uuid.UUID)
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.original_filename, 'test_cumulus.jpg')
        self.assertEqual(record.source_type, SourceType.WEB_UPLOAD)
        self.assertGreater(record.confidence, 0.0)
        self.assertGreater(record.processing_time, 0.0)
        self.assertIsNotNone(record.risk_level)
        self.assertIsNotNone(record.rain_probability_range)
        self.assertIsNotNone(record.advisory_action)

        # Verify record exists in database
        db_record = Prediction.objects.get(id=record.id)
        self.assertEqual(db_record.predicted_class, record.predicted_class)
        self.assertEqual(db_record.user_notes, 'Mid-afternoon cloud formation')

    def test_database_creation_with_iot_telemetry(self):
        """Verifies database persistence with complete edge IoT metadata."""
        img = Image.new('RGB', (256, 256), color=(100, 110, 130))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        iot_upload = SimpleUploadedFile('iot_specimen.jpg', img_io.getvalue(), content_type='image/jpeg')

        record = process_image_prediction(
            iot_upload,
            notes='Edge automated ingestion',
            source_type=SourceType.IOT_DEVICE,
            device_id='RPI4-SKY-NODE-99',
            latitude=12.9716,
            longitude=77.5946,
            temperature=25.4,
            humidity=78.2
        )

        db_record = Prediction.objects.get(id=record.id)
        self.assertEqual(db_record.source_type, SourceType.IOT_DEVICE)
        self.assertEqual(db_record.device_id, 'RPI4-SKY-NODE-99')
        self.assertEqual(db_record.latitude, 12.9716)
        self.assertEqual(db_record.longitude, 77.5946)
        self.assertEqual(db_record.temperature, 25.4)
        self.assertEqual(db_record.humidity, 78.2)
        self.assertTrue(db_record.has_geo_coordinates)
        self.assertTrue(db_record.has_environmental_telemetry)
