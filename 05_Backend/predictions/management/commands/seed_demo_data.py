"""
Management command to seed initial demonstration records from verified test images.
Usage: python manage.py seed_demo_data
"""

from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from predictions.services import process_image_prediction
from predictions.models import PredictionRecord


class Command(BaseCommand):
    help = 'Seeds initial demonstration cloud predictions from verified test splits.'

    def handle(self, *args, **options):
        if PredictionRecord.objects.count() >= 6:
            self.stdout.write(self.style.WARNING(f"Database already contains {PredictionRecord.objects.count()} records. Skipping seed."))
            return

        test_dir = settings.AI_MODEL_DIR / "datasets" / "splits" / "test"
        if not test_dir.exists():
            self.stdout.write(self.style.ERROR(f"Test directory not found at {test_dir}"))
            return

        categories = ["Low_to_Medium_Rain", "Medium_to_Heavy_Rain", "No_to_Low_Rain"]
        seeded = 0

        for cat in categories:
            cat_dir = test_dir / cat
            if not cat_dir.exists():
                continue

            images = list(cat_dir.glob("*.jpg"))[:2]  # Take 2 images per category
            for img_path in images:
                self.stdout.write(f"Processing sample: {img_path.name}...")
                with open(img_path, 'rb') as f:
                    django_file = File(f, name=img_path.name)
                    notes = f"Ground truth category: {cat.replace('_', ' ')} (Verified CCSN test specimen)"
                    record = process_image_prediction(django_file, notes=notes)
                    seeded += 1
                    self.stdout.write(self.style.SUCCESS(f"  -> Predicted: {record.predicted_class} ({record.confidence_percent}%)"))

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {seeded} demonstration predictions."))
