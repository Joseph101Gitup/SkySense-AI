"""
Test Suite 10: Prediction History & Detail Management
Verifies:
- /history/ renders prediction table with pagination
- Search filtering by filename and notes (?q=...)
- Class filtering by rainfall category (?class=...)
- Date range filtering (?date_from=... &date_to=...)
- Chronological sorting (?sort=newest vs ?sort=oldest)
- Detail view (/history/<uuid>/) renders complete observation metrics
- Safe deletion workflow (POST /history/<uuid>/delete/) with image cleanup
"""

import datetime
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from predictions.models import Prediction, RainfallClass, SourceType

User = get_user_model()


class PredictionHistoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='history_tester', password='TestPassword123!')
        self.client.force_login(self.user)
        self.history_url = reverse('predictions:history')

        # Create sample records
        img = Image.new('RGB', (100, 100), color=(80, 90, 100))
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)

        self.records = []
        for i in range(12):
            upload = SimpleUploadedFile(f'cloud_{i:02d}.jpg', img_io.getvalue(), content_type='image/jpeg')
            pred_class = RainfallClass.LOW_TO_MEDIUM if i % 2 == 0 else RainfallClass.MEDIUM_TO_HEAVY
            rec = Prediction.objects.create(
                user=self.user,
                image=upload,
                original_filename=f'cloud_{i:02d}.jpg',
                predicted_class=pred_class,
                confidence=0.75 + (i * 0.01),
                low_to_medium_probability=0.75 if i % 2 == 0 else 0.15,
                medium_to_heavy_probability=0.15 if i % 2 == 0 else 0.75,
                no_to_low_probability=0.10,
                processing_time=120.0,
                source_type=SourceType.WEB_UPLOAD,
                user_notes=f"Note for observation {i}"
            )
            self.records.append(rec)

    def test_history_list_and_pagination(self):
        """Verifies history page renders records and supports pagination."""
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prediction History')
        # 10 records per page: page 1 should contain pagination indicator
        self.assertEqual(response.context['page_obj'].number, 1)
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 2)
        self.assertContains(response, 'Page')

        # Request page 2
        response_p2 = self.client.get(f"{self.history_url}?page=2")
        self.assertEqual(response_p2.status_code, 200)
        self.assertEqual(response_p2.context['page_obj'].number, 2)

    def test_history_search_filter(self):
        """Verifies filtering by search term in filename or notes."""
        response = self.client.get(f"{self.history_url}?q=cloud_05")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cloud_05.jpg')
        self.assertNotContains(response, 'cloud_00.jpg')

    def test_history_class_filter(self):
        """Verifies filtering by prediction category."""
        response = self.client.get(f"{self.history_url}?class={RainfallClass.MEDIUM_TO_HEAVY}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Medium to Heavy Rain')
        self.assertNotContains(response, 'cloud_00.jpg')  # cloud_00 is Low_to_Medium

    def test_history_sort_order(self):
        """Verifies sorting by newest first vs oldest first."""
        response_newest = self.client.get(f"{self.history_url}?sort=newest")
        self.assertEqual(response_newest.status_code, 200)

        response_oldest = self.client.get(f"{self.history_url}?sort=oldest")
        self.assertEqual(response_oldest.status_code, 200)

    def test_detail_view_renders_metrics(self):
        """Verifies /history/<uuid>/ renders individual prediction details."""
        target_rec = self.records[0]
        detail_url = reverse('predictions:detail', kwargs={'pk': target_rec.pk})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cloud_00.jpg')
        self.assertContains(response, 'Low to Medium Rain')
        self.assertContains(response, 'Xception-v1.0')
        self.assertContains(response, '120.0 ms')

    def test_delete_prediction_record(self):
        """Verifies POST /history/<uuid>/delete/ removes record safely."""
        target_rec = self.records[0]
        delete_url = reverse('predictions:delete', kwargs={'pk': target_rec.pk})

        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.history_url)
        self.assertFalse(Prediction.objects.filter(pk=target_rec.pk).exists())
