"""
Context processors for SkySense AI templates.
Provides global system metrics and model status to all templates.
"""

from django.conf import settings

def system_status(request):
    try:
        from predictions.models import PredictionRecord
        total_predictions = PredictionRecord.objects.count()
    except Exception:
        total_predictions = 0

    return {
        'APP_NAME': 'SKYsense AI',
        'SYSTEM_VERSION': 'v1.0.0 (Master Thesis)',
        'ACTIVE_MODEL_NAME': 'Xception Transfer Learning (ImageNet)',
        'MODEL_STATUS': 'Operational',
        'TOTAL_PREDICTIONS_COUNT': total_predictions,
        'MODEL_ACCURACY': '58.27% (Test Set)',
        'DATASET_TOTAL_IMAGES': '2,543',
    }
