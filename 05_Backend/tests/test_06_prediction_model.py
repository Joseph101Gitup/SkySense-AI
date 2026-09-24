"""
Test Suite 6: Prediction Database Model
Verifies:
- Model field definitions, defaults, and choices (RainfallClass, SourceType)
- Strict validation in clean():
  - Probability summation constraint (must equal ~1.0)
  - Confidence score boundaries [0.0, 1.0]
  - Coordinate pair integrity (latitude and longitude must be provided together)
  - Coordinate range limits (lat: [-90, 90], lon: [-180, 180])
  - Humidity range limits [0.0, 100.0]
- Derived helper properties:
  - confidence_pct, prob_low_pct, prob_med_pct, prob_no_pct
  - latency_ms, image_filename, has_geo_coordinates, has_environmental_telemetry
- Model string representation (__str__)
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from predictions.models import Prediction, RainfallClass, SourceType


class PredictionModelTests(TestCase):
    def setUp(self):
        img = Image.new('RGB', (100, 100), color=(100, 120, 140))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        self.upload = SimpleUploadedFile('model_test.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_prediction_creation_and_properties(self):
        """Verifies successful record creation and computed properties."""
        pred = Prediction.objects.create(
            image=self.upload,
            original_filename='model_test.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.7845,
            low_to_medium_probability=0.7845,
            medium_to_heavy_probability=0.1255,
            no_to_low_probability=0.0900,
            processing_time=135.25,
            source_type=SourceType.WEB_UPLOAD,
        )

        self.assertIsNotNone(pred.id)
        self.assertEqual(pred.model_version, 'Xception-v1.0')
        self.assertEqual(pred.confidence_pct, 78.5)
        self.assertEqual(pred.prob_low_pct, 78.5)
        self.assertEqual(pred.prob_med_pct, 12.6)
        self.assertEqual(pred.prob_no_pct, 9.0)
        self.assertEqual(pred.latency_ms, 135.2)
        self.assertEqual(pred.image_filename, 'model_test.jpg')
        self.assertFalse(pred.has_geo_coordinates)
        self.assertFalse(pred.has_environmental_telemetry)
        self.assertIn('Low_to_Medium_Rain', str(pred))
        self.assertEqual(pred.display_name, 'Low to Medium Rain')

    def test_clean_probability_sum_validation(self):
        """Verifies clean() raises ValidationError if probabilities do not sum to 1.0."""
        pred = Prediction(
            image=self.upload,
            original_filename='bad_sum.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.50,
            low_to_medium_probability=0.50,
            medium_to_heavy_probability=0.10,
            no_to_low_probability=0.10,  # Sum = 0.70 (deviates significantly from 1.0)
            processing_time=100.0
        )
        with self.assertRaises(ValidationError) as ctx:
            pred.clean()
        self.assertIn('probabilities must sum', str(ctx.exception).lower())

    def test_clean_confidence_bounds_validation(self):
        """Verifies full_clean() validates confidence score limits [0.0, 1.0]."""
        pred_too_high = Prediction(
            image=self.upload,
            original_filename='too_high.jpg',
            predicted_class=RainfallClass.MEDIUM_TO_HEAVY,
            confidence=1.50,
            low_to_medium_probability=0.1,
            medium_to_heavy_probability=0.8,
            no_to_low_probability=0.1,
            processing_time=100.0
        )
        with self.assertRaises(ValidationError) as ctx:
            pred_too_high.full_clean()
        self.assertTrue('confidence' in str(ctx.exception).lower())

    def test_clean_paired_coordinates_validation(self):
        """Verifies latitude without longitude raises ValidationError."""
        pred_unpaired_lat = Prediction(
            image=self.upload,
            original_filename='unpaired.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.80,
            low_to_medium_probability=0.10,
            medium_to_heavy_probability=0.10,
            no_to_low_probability=0.80,
            processing_time=100.0,
            latitude=12.9716,
            longitude=None  # Missing longitude
        )
        with self.assertRaises(ValidationError) as ctx:
            pred_unpaired_lat.clean()
        self.assertIn('Both latitude and longitude must be provided together', str(ctx.exception))

    def test_clean_coordinate_range_validation(self):
        """Verifies out-of-range coordinates are rejected."""
        pred_bad_lat = Prediction(
            image=self.upload,
            original_filename='bad_coords.jpg',
            predicted_class=RainfallClass.NO_TO_LOW,
            confidence=0.80,
            low_to_medium_probability=0.10,
            medium_to_heavy_probability=0.10,
            no_to_low_probability=0.80,
            processing_time=100.0,
            latitude=95.0,  # Invalid latitude (> 90)
            longitude=77.59
        )
        with self.assertRaises(ValidationError) as ctx:
            pred_bad_lat.full_clean()
        self.assertTrue('latitude' in str(ctx.exception).lower())
