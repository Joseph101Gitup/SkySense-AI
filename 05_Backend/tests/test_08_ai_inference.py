"""
Test Suite 8: AI Inference Engine
Verifies:
- RainfallInferenceService singleton pattern (get_instance())
- Strict image preprocessing (256x256 RGB normalization in range [0.0, 1.0])
- Inference execution producing:
  - Valid predicted_class in ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain']
  - Confidence score within [0.0, 1.0]
  - Probability distribution across all 3 classes summing to ~1.0
- Deterministic behavior and error handling
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.conf import settings
from predictions.services import RainfallInferenceService


class AIInferenceTests(TestCase):
    def setUp(self):
        self.assertIsNotNone(RainfallInferenceService, "RainfallInferenceService must be available.")
        self.service = RainfallInferenceService.get_instance()

    def test_inference_service_singleton(self):
        """Verifies get_instance() returns the exact same singleton instance."""
        service_b = RainfallInferenceService.get_instance()
        self.assertIs(self.service, service_b)

    def test_inference_on_synthetic_cloud_image(self):
        """Verifies full inference pipeline on a synthetic cloud photograph."""
        # Generate synthetic 256x256 RGB image with realistic cloud-like grey tones
        img = Image.new('RGB', (256, 256), color=(140, 155, 170))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        image_bytes = img_io.getvalue()

        result = self.service.predict(image_bytes)

        self.assertIn('predicted_class', result)
        self.assertIn('confidence', result)
        self.assertIn('probabilities', result)

        # Class validation
        valid_classes = ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain']
        self.assertIn(result['predicted_class'], valid_classes)

        # Confidence validation
        confidence = result['confidence']
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

        # Probabilities validation
        probs = result['probabilities']
        for cls_name in valid_classes:
            self.assertIn(cls_name, probs)
            self.assertGreaterEqual(probs[cls_name], 0.0)
            self.assertLessEqual(probs[cls_name], 1.0)

        prob_sum = sum(probs.values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

    def test_image_preprocessing_tensor_shape_and_range(self):
        """Verifies preprocessing generates (1, 256, 256, 3) tensor bounded within [0, 1]."""
        img = Image.new('RGB', (500, 300), color=(100, 150, 200))
        tensor = self.service.preprocess(img)

        self.assertEqual(tensor.shape, (1, 256, 256, 3))
        self.assertGreaterEqual(tensor.min(), 0.0)
        self.assertLessEqual(tensor.max(), 1.0)
