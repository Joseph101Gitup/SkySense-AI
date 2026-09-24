"""
Tests for Core App: Dashboard real-time telemetry, Chart.js integrations, and empty state support.
"""

from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth import get_user_model
from predictions.models import Prediction, RainfallClass, SourceType

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dash_tester', password='PassWord123!')
        self.client.force_login(self.user)

    def test_dashboard_empty_state(self):
        """Verifies dashboard renders graceful empty state when database has 0 records."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Cloud Specimen Analyses Logged Yet')
        self.assertContains(response, 'None Yet')
        self.assertContains(response, 'Analyze New Image')

        # Test API empty state
        api_res = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data['total_analyses'], 0)
        self.assertEqual(data['today_analyses'], 0)
        self.assertEqual(data['average_confidence_pct'], 0.0)
        self.assertIsNone(data['most_recent'])

    def test_dashboard_populated_telemetry_and_charts(self):
        """Verifies dashboard displays real database statistics and populated charts."""
        img = Image.new('RGB', (256, 256), color=(80, 100, 120))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        upload = SimpleUploadedFile('dash_cloud.jpg', img_io.getvalue(), content_type='image/jpeg')

        pred = Prediction.objects.create(
            user=self.user,
            image=upload,
            original_filename='dash_cloud.jpg',
            predicted_class=RainfallClass.LOW_TO_MEDIUM,
            confidence=0.765,
            low_to_medium_probability=0.765,
            medium_to_heavy_probability=0.155,
            no_to_low_probability=0.080,
            processing_time=110.2,
            source_type=SourceType.WEB_UPLOAD
        )

        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Analyses')
        self.assertContains(response, "Today's Analyses")
        self.assertContains(response, 'Average Confidence')
        self.assertContains(response, 'Most Recent Prediction')
        self.assertContains(response, 'dash_cloud.jpg')
        self.assertContains(response, '76.5%')
        self.assertContains(response, 'Low to Medium Rain')
        self.assertContains(response, 'Analyze New Image')

        # Verify API response
        api_res = self.client.get(reverse('core:api_dashboard_stats'))
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data['total_analyses'], 1)
        self.assertEqual(data['today_analyses'], 1)
        self.assertEqual(data['average_confidence_pct'], 76.5)
        self.assertIsNotNone(data['most_recent'])
        self.assertEqual(data['most_recent']['original_filename'], 'dash_cloud.jpg')
        self.assertEqual(data['rainfall_distribution']['Low_to_Medium_Rain'], 1)
        self.assertIn('timeline', data)
        self.assertIn('confidence_distribution', data)


class ModelPerformanceTests(TestCase):
    """
    Test suite for academic Model Performance page.
    Verifies actual evaluation metrics, confusion matrix, training curves,
    dataset distribution, and methodology documentation.
    """

    def setUp(self):
        self.client = Client()

    def test_model_performance_view_renders_actual_metrics(self):
        """Verifies that /performance/ and /metrics/ display real evaluation metrics."""
        for route_name in ['core:model_performance', 'core:research_metrics']:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)

            # Title
            self.assertContains(response, 'Model Performance')

            # 1. Headline Metrics
            self.assertContains(response, '58.27%')   # Test accuracy
            self.assertContains(response, '61.23%')   # Macro precision
            self.assertContains(response, '55.74%')   # Macro recall
            self.assertContains(response, '56.60%')   # Macro F1
            self.assertContains(response, '0.9103')   # Test loss

            # 2. Confusion Matrix
            self.assertContains(response, 'Confusion Matrix')
            self.assertContains(response, '108')
            self.assertContains(response, '36')
            self.assertContains(response, '78')

            # 3. Class-wise precision, recall, F1
            self.assertContains(response, 'Class-Wise Evaluation Breakdown')
            self.assertContains(response, 'Low to Medium Rain')
            self.assertContains(response, 'Medium to Heavy Rain')
            self.assertContains(response, 'No to Low Rain')
            self.assertContains(response, '54.0%')   # Class 0 precision
            self.assertContains(response, '72.0%')   # Class 0 recall
            self.assertContains(response, '61.71%')  # Class 0 F1

            # 4. Training / Validation accuracy & loss curves
            self.assertContains(response, 'accuracyChart')
            self.assertContains(response, 'lossChart')
            self.assertContains(response, '64.14%')  # Best val acc
            self.assertContains(response, '0.8569')  # Best val loss

            # 5. Dataset distribution
            self.assertContains(response, '2,543 Total Images')
            self.assertContains(response, '1,004')
            self.assertContains(response, '624')
            self.assertContains(response, '915')
            self.assertContains(response, '1,779')   # Train split
            self.assertContains(response, '383')     # Val split
            self.assertContains(response, '381')     # Test split

            # 6. Methodology
            self.assertContains(response, 'Methodology')
            self.assertContains(response, 'Dataset Architecture')
            self.assertContains(response, 'Preprocessing &amp; Augmentation')
            self.assertContains(response, 'Transfer Learning Paradigm')
            self.assertContains(response, 'Xception Backbone')
            self.assertContains(response, 'Phase 1 Training')
            self.assertContains(response, 'Phase 2 Fine-Tuning')
            self.assertContains(response, 'Empirical Evaluation Protocol')

            # 7. Scientific statement
            self.assertContains(response, 'predicts')
            self.assertContains(response, 'rainfall')
            self.assertContains(response, 'NOT a cloud-type')


class LandingPageTests(TestCase):
    """
    Test suite for the professional SKYsense AI landing page.
    Verifies Hero, How SKYsense AI works, AI capabilities, Technology,
    Research, Future architecture (FUTURE WORK), and Footer requirements.
    """

    def setUp(self):
        self.client = Client()

    def test_landing_page_renders_all_mandatory_sections(self):
        """Verifies that / renders all sections and content specified in the requirements."""
        response = self.client.get(reverse('core:landing'))
        self.assertEqual(response.status_code, 200)

        # 1. Hero
        self.assertContains(response, 'SKYsense')
        self.assertContains(response, 'AI-Powered Cloud &amp; Rainfall Intelligence')
        self.assertContains(response, 'Analyze cloud imagery using deep learning to estimate rainfall conditions.')
        self.assertContains(response, 'Analyze an Image')
        self.assertContains(response, 'Explore Dashboard')

        # 2. Section 1: How SKYsense AI works
        self.assertContains(response, 'How SKYsense AI Works')
        self.assertContains(response, 'AI Preprocessing')
        self.assertContains(response, 'Xception Model')
        self.assertContains(response, 'Rainfall Classification')
        self.assertContains(response, 'Interactive Dashboard')

        # 3. Section 2: AI capabilities
        self.assertContains(response, 'AI Capabilities')
        self.assertContains(response, 'Image Analysis')
        self.assertContains(response, 'Rainfall Classification')
        self.assertContains(response, 'Confidence Estimation')
        self.assertContains(response, 'Historical Analysis')

        # 4. Section 3: Technology
        self.assertContains(response, 'Technology Stack')
        self.assertContains(response, 'Python')
        self.assertContains(response, 'TensorFlow / Keras')
        self.assertContains(response, 'Xception')
        self.assertContains(response, 'Django')
        self.assertContains(response, 'SQLite')
        self.assertContains(response, 'JavaScript')
        self.assertContains(response, 'Chart.js')

        # 5. Section 4: Research
        self.assertContains(response, 'Research &amp; Methodology')
        self.assertContains(response, 'Dataset')
        self.assertContains(response, 'Model Architecture')
        self.assertContains(response, 'Evaluation')
        self.assertContains(response, 'Future IoT Integration')

        # 6. Section 5: Future architecture (clearly labeled as FUTURE WORK)
        self.assertContains(response, 'Future Architecture')
        self.assertContains(response, 'Cloud Image')
        self.assertContains(response, 'IoT Camera / Device')
        self.assertContains(response, 'API')
        self.assertContains(response, 'AI Model')
        self.assertContains(response, 'SKYsense Dashboard')
        self.assertContains(response, 'Future Work')

        # 7. Section 6: Footer
        self.assertContains(response, "Master's Degree Project")
        self.assertContains(response, 'AI + Cloud Computing + Future IoT Integration')


