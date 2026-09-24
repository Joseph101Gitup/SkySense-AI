from pathlib import Path
import json
import csv
import logging
import datetime
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.utils import timezone
from django.http import JsonResponse

from predictions.models import Prediction, PredictionRecord

logger = logging.getLogger(__name__)


def landing_view(request):
    """Modern public landing page with product hero and feature highlights."""
    recent_predictions = Prediction.objects.all().order_by('-created_at')[:3]
    total_count = Prediction.objects.count()
    return render(request, 'core/landing.html', {
        'recent_predictions': recent_predictions,
        'total_count': total_count,
        'page_title': 'Precision Weather Intelligence',
    })


@login_required
def dashboard_view(request):
    """
    Main real-time analytics dashboard:
    - Dynamic KPI cards (TOTAL ANALYSES, TODAY'S ANALYSES, AVERAGE CONFIDENCE, MOST RECENT PREDICTION)
    - 3 Chart.js Visualizations (Rainfall Category Split, Activity Timeline, Confidence Distribution)
    - Recent Inferences Table
    - Visually impressive layout with graceful zero-state support
    - Scoped to user's predictions; admin/staff see all records
    """
    today = timezone.now().date()
    is_admin = request.user.is_staff or request.user.is_superuser
    if is_admin:
        base_qs = Prediction.objects.all()
    else:
        base_qs = Prediction.objects.filter(user=request.user)

    # 1. Core KPIs
    total_analyses = base_qs.count()
    today_analyses = base_qs.filter(created_at__date=today).count()
    avg_confidence = base_qs.aggregate(avg=Avg('confidence'))['avg']
    avg_conf_pct = round(avg_confidence * 100, 1) if avg_confidence is not None else 0.0
    most_recent = base_qs.order_by('-created_at').first()

    # 2. Chart 1: Predictions by rainfall category
    counts_map = {
        'Low_to_Medium_Rain': base_qs.filter(predicted_class='Low_to_Medium_Rain').count(),
        'Medium_to_Heavy_Rain': base_qs.filter(predicted_class='Medium_to_Heavy_Rain').count(),
        'No_to_Low_Rain': base_qs.filter(predicted_class='No_to_Low_Rain').count(),
    }

    # Dominant trend
    dominant_class = max(counts_map, key=counts_map.get) if total_analyses > 0 else "None"

    # 3. Chart 2: Predictions over time (last 7 calendar days)
    timeline_labels = []
    timeline_data = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_count = base_qs.filter(created_at__date=day).count()
        timeline_labels.append(day.strftime("%b %d"))
        timeline_data.append(day_count)

    # 4. Chart 3: Confidence distribution
    conf_below_50 = base_qs.filter(confidence__lt=0.50).count()
    conf_50_60 = base_qs.filter(confidence__gte=0.50, confidence__lt=0.60).count()
    conf_60_70 = base_qs.filter(confidence__gte=0.60, confidence__lt=0.70).count()
    conf_70_85 = base_qs.filter(confidence__gte=0.70, confidence__lt=0.85).count()
    conf_85_100 = base_qs.filter(confidence__gte=0.85).count()
    confidence_labels = ['< 50%', '50-60%', '60-70%', '70-85%', '85-100%']
    confidence_data = [conf_below_50, conf_50_60, conf_60_70, conf_70_85, conf_85_100]

    # 5. Recent predictions
    recent_predictions = base_qs.order_by('-created_at')[:8]

    context = {
        'page_title': 'Meteorological Intelligence Dashboard',
        'is_admin': is_admin,
        'total_analyses': total_analyses,
        'today_analyses': today_analyses,
        'avg_conf_pct': avg_conf_pct,
        'most_recent': most_recent,
        'dominant_class': dominant_class,
        'counts_map': counts_map,
        'timeline_labels_json': json.dumps(timeline_labels),
        'timeline_data_json': json.dumps(timeline_data),
        'confidence_labels_json': json.dumps(confidence_labels),
        'confidence_data_json': json.dumps(confidence_data),
        'recent_predictions': recent_predictions,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def api_dashboard_stats(request):
    """
    REST API endpoint providing real-time dashboard telemetry from SQLite.
    GET /api/dashboard/stats/
    """
    today = timezone.now().date()
    is_admin = request.user.is_staff or request.user.is_superuser
    if is_admin:
        base_qs = Prediction.objects.all()
    else:
        base_qs = Prediction.objects.filter(user=request.user)

    total_analyses = base_qs.count()
    today_analyses = base_qs.filter(created_at__date=today).count()
    avg_confidence = base_qs.aggregate(avg=Avg('confidence'))['avg']
    avg_conf_pct = round(avg_confidence * 100, 1) if avg_confidence is not None else 0.0
    most_recent = base_qs.order_by('-created_at').first()

    counts_map = {
        'Low_to_Medium_Rain': base_qs.filter(predicted_class='Low_to_Medium_Rain').count(),
        'Medium_to_Heavy_Rain': base_qs.filter(predicted_class='Medium_to_Heavy_Rain').count(),
        'No_to_Low_Rain': base_qs.filter(predicted_class='No_to_Low_Rain').count(),
    }

    timeline_labels = []
    timeline_data = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        timeline_labels.append(day.strftime("%b %d"))
        timeline_data.append(base_qs.filter(created_at__date=day).count())

    confidence_labels = ['< 50%', '50-60%', '60-70%', '70-85%', '85-100%']
    confidence_data = [
        base_qs.filter(confidence__lt=0.50).count(),
        base_qs.filter(confidence__gte=0.50, confidence__lt=0.60).count(),
        base_qs.filter(confidence__gte=0.60, confidence__lt=0.70).count(),
        base_qs.filter(confidence__gte=0.70, confidence__lt=0.85).count(),
        base_qs.filter(confidence__gte=0.85).count(),
    ]

    return JsonResponse({
        'total_analyses': total_analyses,
        'today_analyses': today_analyses,
        'average_confidence_pct': avg_conf_pct,
        'most_recent': most_recent.to_dict() if most_recent else None,
        'rainfall_distribution': counts_map,
        'timeline': {
            'labels': timeline_labels,
            'counts': timeline_data,
        },
        'confidence_distribution': {
            'labels': confidence_labels,
            'counts': confidence_data,
        },
        'server_timestamp': timezone.now().isoformat(),
    })


def about_view(request):
    """About page outlining Master's final year project details."""
    context = {
        'page_title': 'About SKYsense AI',
        'project_title': 'SKYsense AI - Cloud-Image Rainfall Classification System',
        'degree': "Master's Final-Year Project",
        'institution': 'Academic Project Showcase',
        'year': '2026',
    }
    return render(request, 'core/about.html', context)


def model_info_view(request):
    """
    Detailed technical specification of the deep learning model.
    Highlights Xception transfer learning, input specs, and critical scientific disclosure.
    """
    context = {
        'page_title': 'AI Model Architecture',
        'model_name': 'Xception Transfer Learning (ImageNet)',
        'parameters_total': '20,867,627 (79.60 MB)',
        'parameters_trainable_phase1': '6,147 (24.01 KB)',
        'input_resolution': '256 × 256 RGB',
        'normalization': '0.0 to 1.0 (rescale = 1/255.0)',
        'batch_size': '32',
        'backbone': 'Xception (Chollet, 2017)',
        'pooling': 'GlobalAveragePooling2D',
        'dropout': '0.40',
        'output_classes': 3,
        'classes': [
            {'index': 0, 'name': 'Low_to_Medium_Rain', 'clouds': 'Altostratus (As), Stratocumulus (Sc), Stratus (St), Nimbostratus (Ns)'},
            {'index': 1, 'name': 'Medium_to_Heavy_Rain', 'clouds': 'Cumulonimbus (Cb), Cumulus (Cu), Cirrostratus thick (Ct)'},
            {'index': 2, 'name': 'No_to_Low_Rain', 'clouds': 'Cirrus (Ci), Cirrostratus (Cs), Cirrocumulus (Cc), Altocumulus (Ac)'},
        ]
    }
    return render(request, 'core/model_info.html', context)


def load_actual_evaluation_data():
    """
    Reads actual saved evaluation results and training logs generated by the AI training pipeline.
    Never invents or hardcodes fabricated metrics.
    If the files do not exist or are invalid, returns None.
    """
    ai_dir = Path(settings.BASE_DIR).parent / '03_AI_Model'
    summary_path = ai_dir / 'evaluation' / 'test_evaluation_summary.json'
    report_path = ai_dir / 'evaluation' / 'classification_report.json'
    log_path = ai_dir / 'logs' / 'training_log.csv'

    if not summary_path.is_file() or not report_path.is_file():
        logger.warning(f"Evaluation files missing at {summary_path} or {report_path}")
        return None

    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)

        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read evaluation JSON: {e}")
        return None

    # Parse primary evaluation metrics directly from actual files
    test_accuracy = summary.get('test_accuracy', 0.0)
    test_loss = summary.get('test_loss', 0.0)
    total_test_samples = summary.get('total_test_samples', 0)

    # Read macro and weighted averages from classification report
    macro_avg = report.get('macro avg', {})
    weighted_avg = report.get('weighted avg', {})

    macro_precision = macro_avg.get('precision', 0.0)
    macro_recall = macro_avg.get('recall', 0.0)
    macro_f1 = macro_avg.get('f1-score', summary.get('macro_avg_f1', 0.0))

    weighted_precision = weighted_avg.get('precision', 0.0)
    weighted_recall = weighted_avg.get('recall', 0.0)
    weighted_f1 = weighted_avg.get('f1-score', summary.get('weighted_avg_f1', 0.0))

    # Class breakdown from actual classification report
    dataset_totals = {
        'Low_to_Medium_Rain': 1004,
        'Medium_to_Heavy_Rain': 624,
        'No_to_Low_Rain': 915,
    }
    badge_colors = {
        'Low_to_Medium_Rain': 'amber',
        'Medium_to_Heavy_Rain': 'rose',
        'No_to_Low_Rain': 'emerald',
    }

    class_breakdown = []
    class_order = ['Low_to_Medium_Rain', 'Medium_to_Heavy_Rain', 'No_to_Low_Rain']
    for cls in class_order:
        cls_data = report.get(cls, {})
        prec = cls_data.get('precision', 0.0)
        rec = cls_data.get('recall', 0.0)
        f1 = cls_data.get('f1-score', 0.0)
        supp = cls_data.get('support', 0)
        class_breakdown.append({
            'name': cls,
            'display_name': cls.replace('_', ' '),
            'precision': round(prec * 100, 2),
            'recall': round(rec * 100, 2),
            'f1': round(f1 * 100, 2),
            'support': supp,
            'total_count': dataset_totals.get(cls, 0),
            'badge_color': badge_colors.get(cls, 'slate'),
        })

    # Confusion matrix from test_evaluation_summary.json
    raw_cm = summary.get('confusion_matrix', [])
    confusion_matrix = []
    if len(raw_cm) == 3:
        cm_labels = ['Low to Medium Rain', 'Medium to Heavy Rain', 'No to Low Rain']
        for i, row in enumerate(raw_cm):
            row_sum = sum(row)
            confusion_matrix.append({
                'true_label': cm_labels[i],
                'pred_low': row[0],
                'pred_low_pct': round((row[0] / row_sum * 100), 1) if row_sum else 0,
                'pred_med': row[1],
                'pred_med_pct': round((row[1] / row_sum * 100), 1) if row_sum else 0,
                'pred_no': row[2],
                'pred_no_pct': round((row[2] / row_sum * 100), 1) if row_sum else 0,
                'total': row_sum,
            })

    # Read training log history if available
    training_epochs = []
    train_acc_list = []
    val_acc_list = []
    train_loss_list = []
    val_loss_list = []

    if log_path.is_file():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    epoch_num = int(row.get('epoch', 0)) + 1
                    training_epochs.append(f"Epoch {epoch_num}")
                    train_acc_list.append(round(float(row.get('accuracy', 0)) * 100, 2))
                    val_acc_list.append(round(float(row.get('val_accuracy', 0)) * 100, 2))
                    train_loss_list.append(round(float(row.get('loss', 0)), 4))
                    val_loss_list.append(round(float(row.get('val_loss', 0)), 4))
        except Exception as e:
            logger.warning(f"Failed to read training_log.csv: {e}")

    # Dataset distribution
    dataset_distribution = {
        'total_size': 2543,
        'classes': [
            {'name': 'Low to Medium Rain', 'key': 'Low_to_Medium_Rain', 'count': 1004, 'percentage': 39.5, 'color': '#fbbf24'},
            {'name': 'Medium to Heavy Rain', 'key': 'Medium_to_Heavy_Rain', 'count': 624, 'percentage': 24.5, 'color': '#f43f5e'},
            {'name': 'No to Low Rain', 'key': 'No_to_Low_Rain', 'count': 915, 'percentage': 36.0, 'color': '#10b981'},
        ],
        'splits': [
            {'name': 'Training Partition', 'percentage': 70, 'count': 1779},
            {'name': 'Validation Partition', 'percentage': 15, 'count': 383},
            {'name': 'Independent Test Set', 'percentage': 15, 'count': 381},
        ],
        'chart_labels_json': json.dumps(['Low to Medium Rain', 'Medium to Heavy Rain', 'No to Low Rain']),
        'chart_counts_json': json.dumps([1004, 624, 915]),
    }

    return {
        'test_accuracy_pct': round(test_accuracy * 100, 2),
        'test_loss': round(test_loss, 4),
        'total_test_samples': total_test_samples,
        'macro_precision_pct': round(macro_precision * 100, 2),
        'macro_recall_pct': round(macro_recall * 100, 2),
        'macro_f1_pct': round(macro_f1 * 100, 2),
        'weighted_precision_pct': round(weighted_precision * 100, 2),
        'weighted_recall_pct': round(weighted_recall * 100, 2),
        'weighted_f1_pct': round(weighted_f1 * 100, 2),
        'class_breakdown': class_breakdown,
        'confusion_matrix': confusion_matrix,
        'training_history': {
            'epochs_json': json.dumps(training_epochs),
            'train_acc_json': json.dumps(train_acc_list),
            'val_acc_json': json.dumps(val_acc_list),
            'train_loss_json': json.dumps(train_loss_list),
            'val_loss_json': json.dumps(val_loss_list),
            'has_history': len(training_epochs) > 0,
        },
        'dataset_distribution': dataset_distribution,
    }


def model_performance_view(request):
    """
    Academic demonstration page displaying actual evaluation metrics generated
    by the AI training pipeline (Test Accuracy, Precision, Recall, F1, Confusion Matrix,
    Class-wise metrics, Training/Validation Loss & Accuracy curves, and Dataset Distribution).
    If metrics do not exist yet, displays: 'Model evaluation data is not available.'
    """
    evaluation_data = load_actual_evaluation_data()

    context = {
        'page_title': 'Model Performance & Evaluation Suite',
        'metrics_available': evaluation_data is not None,
        'data': evaluation_data,
    }
    return render(request, 'core/model_performance.html', context)


# Backward-compatible alias for existing templates and tests
research_metrics_view = model_performance_view

