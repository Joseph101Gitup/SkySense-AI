import uuid
import json
import datetime
import logging
from pathlib import Path
from PIL import Image

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, FileResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.files import File
from django.db.models import Q
from django.utils import timezone

from .models import PredictionRecord
from .forms import ImagePredictionForm
from .services import (
    process_image_prediction,
    get_sample_test_images,
    METEOROLOGICAL_ADVISORIES,
    InferenceError,
    InvalidImageFormatError,
    CorruptedImageError,
    FileTooLargeError,
)


import logging

logger = logging.getLogger(__name__)


@login_required
def predict_view(request):
    """
    Image prediction submission page.
    Provides drag-and-drop file upload, file validation, and verified sample images gallery.
    """
    sample_images = get_sample_test_images()

    if request.method == 'POST':
        form = ImagePredictionForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data['image']
            notes = form.cleaned_data.get('notes', '')

            try:
                record = process_image_prediction(image_file, notes=notes, user=request.user)
                messages.success(request, f"Cloud image successfully analyzed: {record.display_name}")
                return redirect('predictions:result', pk=record.pk)
            except InvalidImageFormatError as e:
                logger.warning(f"Invalid format uploaded: {e}")
                messages.error(request, "Unsupported file format. Please upload a valid JPG, JPEG, or PNG photograph.")
            except CorruptedImageError as e:
                logger.warning(f"Corrupted image uploaded: {e}")
                messages.error(request, "The uploaded image appears corrupted or incomplete. Please upload an intact image.")
            except FileTooLargeError as e:
                logger.warning(f"Payload too large: {e}")
                messages.error(request, "Image file size exceeds the 15 MB limit. Please select a smaller photograph.")
            except InferenceError as e:
                logger.error(f"Inference error: {e}")
                messages.error(request, "The AI inference engine encountered an issue evaluating the image. Please try again.")
            except Exception as e:
                logger.exception("Unexpected error during cloud image prediction")
                messages.error(request, "An unexpected error occurred while analyzing the image. Please try again.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ImagePredictionForm()

    return render(request, 'predictions/predict.html', {
        'form': form,
        'sample_images': sample_images,
        'page_title': 'Analyze Cloud Image',
    })


@login_required
@require_POST
def predict_sample_view(request):
    """
    Instantly runs prediction on one of the verified sample test images from the dataset.
    Allows one-click demonstration without requiring manual file upload.
    Secured against Path Traversal by enforcing path boundaries.
    """
    sample_path_str = request.POST.get('sample_path')
    if not sample_path_str:
        messages.error(request, "No sample image specified.")
        return redirect('predictions:predict')

    sample_path = Path(sample_path_str).resolve()
    valid_test_dir = (settings.AI_MODEL_DIR / 'datasets' / 'splits' / 'test').resolve()
    valid_demo_dir = (settings.BASE_DIR.parent / 'demo_images').resolve()

    # Path traversal protection: Ensure the resolved path is strictly within valid_test_dir or valid_demo_dir
    is_valid_test = sample_path.is_relative_to(valid_test_dir) if valid_test_dir.exists() else False
    is_valid_demo = sample_path.is_relative_to(valid_demo_dir) if valid_demo_dir.exists() else False

    if not (is_valid_test or is_valid_demo):
        logger.warning(f"Path traversal attempt blocked: {sample_path_str}")
        messages.error(request, "Access denied: Invalid sample image path.")
        return redirect('predictions:predict')

    if not sample_path.exists() or not sample_path.is_file():
        messages.error(request, "Selected sample image does not exist on disk.")
        return redirect('predictions:predict')

    try:
        with open(sample_path, 'rb') as f:
            django_file = File(f, name=sample_path.name)
            record = process_image_prediction(
                django_file,
                notes=f"Evaluated from verified sample dataset specimen: {sample_path.name}",
                user=request.user
            )
        messages.success(request, f"Sample specimen analyzed successfully: {record.display_name}")
        return redirect('predictions:result', pk=record.pk)
    except Exception:
        logger.exception("Error analyzing sample image")
        messages.error(request, "Unable to evaluate the selected sample image. Please try another.")
        return redirect('predictions:predict')


@login_required
def result_view(request, pk):
    """
    Prediction result page presenting:
    - Predicted rainfall class with stylized visual badge
    - Confidence meter
    - Class probability breakdown
    - Meteorological context & advisory recommendations
    """
    record = get_object_or_404(PredictionRecord, pk=pk)

    # Permission check: users only view their own predictions; admin can view all
    if not (request.user.is_staff or request.user.is_superuser) and record.user != request.user:
        return HttpResponseForbidden("You do not have permission to view this prediction result.")

    return render(request, 'predictions/result.html', {
        'record': record,
        'page_title': f"Result: {record.display_name}",
    })


@login_required
def history_view(request):
    """
    Searchable, filterable list of previous rainfall predictions.
    Users only see their own prediction history.
    Admin/staff users can see all predictions across the system.
    Supports:
    - Search by filename, user notes, UUID
    - Category filtering (3 classes)
    - Date range filtering (preset or custom date range)
    - Sorting (newest, oldest, highest confidence, lowest confidence)
    - Pagination preserving active query parameters
    """
    is_admin = request.user.is_staff or request.user.is_superuser
    if is_admin:
        queryset = PredictionRecord.objects.all()
    else:
        queryset = PredictionRecord.objects.filter(user=request.user)

    # Category Filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter and category_filter != 'all':
        queryset = queryset.filter(predicted_class=category_filter)

    # Search Query
    search_query = request.GET.get('q', '').strip()
    if search_query:
        query_filter = Q(original_filename__icontains=search_query) | Q(user_notes__icontains=search_query)
        try:
            uuid_val = uuid.UUID(search_query)
            query_filter |= Q(id=uuid_val)
        except ValueError:
            pass
        queryset = queryset.filter(query_filter)

    # Date Range Preset Filter
    date_preset = request.GET.get('date_range', '').strip()
    now_date = timezone.now().date()
    if date_preset == 'today':
        queryset = queryset.filter(created_at__date=now_date)
    elif date_preset == 'yesterday':
        queryset = queryset.filter(created_at__date=now_date - datetime.timedelta(days=1))
    elif date_preset == 'last_7_days':
        queryset = queryset.filter(created_at__date__gte=now_date - datetime.timedelta(days=7))
    elif date_preset == 'last_30_days':
        queryset = queryset.filter(created_at__date__gte=now_date - datetime.timedelta(days=30))

    # Custom Date Range (from / to)
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()

    if date_from_str:
        try:
            date_from = datetime.datetime.strptime(date_from_str, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = datetime.datetime.strptime(date_to_str, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'highest_confidence':
        queryset = queryset.order_by('-confidence')
    elif sort_by == 'lowest_confidence':
        queryset = queryset.order_by('confidence')
    elif sort_by == 'oldest':
        queryset = queryset.order_by('created_at')
    else:
        queryset = queryset.order_by('-created_at')

    # Pagination (10 per page)
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'predictions/history.html', {
        'page_obj': page_obj,
        'current_category': category_filter,
        'search_query': search_query,
        'current_sort': sort_by,
        'date_preset': date_preset,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'total_count': queryset.count(),
        'is_admin': is_admin,
        'page_title': 'Prediction History & Archives',
    })


@login_required
def detail_view(request, pk):
    """Full detail view for a specific historical prediction."""
    record = get_object_or_404(PredictionRecord, pk=pk)

    # Permission check: users only view/edit their own predictions; admin can view all
    if not (request.user.is_staff or request.user.is_superuser) and record.user != request.user:
        return HttpResponseForbidden("You do not have permission to access this prediction.")

    if request.method == 'POST':
        # Update user notes
        notes = request.POST.get('user_notes', '')
        record.user_notes = notes
        record.save()
        messages.success(request, "Observation notes updated successfully.")
        return redirect('predictions:detail', pk=record.pk)

    return render(request, 'predictions/detail.html', {
        'record': record,
        'page_title': f"Prediction Details - {record.original_filename}",
    })


@login_required
@require_POST
def delete_view(request, pk):
    """
    Deletes a prediction record with strict security validations:
    - Verifies user ownership (or admin privileges)
    - Never allows path traversal or unsafe file access outside MEDIA_ROOT
    - Deletes database entity
    """
    record = get_object_or_404(PredictionRecord, pk=pk)

    # Permission check: users only delete their own predictions; admin can delete any
    if not (request.user.is_staff or request.user.is_superuser) and record.user != request.user:
        return HttpResponseForbidden("You do not have permission to delete this prediction record.")

    filename = record.original_filename

    # Safe file system cleanup
    if record.image:
        try:
            media_root = Path(settings.MEDIA_ROOT).resolve()
            image_path = Path(record.image.path).resolve()
            # Ensure path is strictly confined to MEDIA_ROOT
            if image_path.is_relative_to(media_root) and image_path.is_file():
                record.image.delete(save=False)
        except Exception as e:
            logger.warning(f"File cleanup skipped or handled for {filename}: {e}")

    record.delete()
    messages.success(request, f"Prediction record for '{filename}' successfully removed.")
    return redirect('predictions:history')


@csrf_exempt
@require_POST
def api_predict_view(request):
    """
    REST-style API endpoint for future IoT integration and programmatic clients.
    POST /api/predict/ with multipart/form-data containing mandatory 'image' parameter,
    plus optional future IoT metadata: device_id, latitude, longitude, temperature, humidity.
    """
    if 'image' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'Missing required parameter: "image" must be provided in multipart/form-data.'
        }, status=400)

    image_file = request.FILES['image']
    
    # Extension validation
    ext = Path(image_file.name).suffix.lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return JsonResponse({
            'success': False,
            'error': f'Unsupported file format "{ext}". Please upload a valid JPG, JPEG, or PNG photograph.'
        }, status=400)

    # Size limit validation
    if image_file.size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return JsonResponse({
            'success': False,
            'error': f'Image file size exceeds the {max_mb:.0f} MB limit. Please select a smaller photograph.'
        }, status=400)

    # MIME type validation
    if hasattr(image_file, 'content_type') and image_file.content_type:
        if image_file.content_type not in settings.ALLOWED_IMAGE_MIME_TYPES:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported MIME type "{image_file.content_type}". Allowed MIME types: {", ".join(settings.ALLOWED_IMAGE_MIME_TYPES)}.'
            }, status=400)

    # Deep binary verification with PIL
    try:
        image_file.seek(0)
        with Image.open(image_file) as pil_img:
            pil_img.verify()
            if pil_img.format not in ['JPEG', 'PNG']:
                return JsonResponse({
                    'success': False,
                    'error': f'Image content format "{pil_img.format}" is not supported. Only JPEG and PNG are allowed.'
                }, status=400)
        image_file.seek(0)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Uploaded file is corrupted or not a valid image: {e}'
        }, status=400)

    notes = request.POST.get('notes', 'IoT / API Automated Ingestion')
    user = request.user if request.user.is_authenticated else None

    # Parse optional IoT metadata
    device_id = request.POST.get('device_id', '').strip() or None
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    temperature_raw = request.POST.get('temperature', '').strip()
    humidity_raw = request.POST.get('humidity', '').strip()

    # Determine source_type: IOT_DEVICE if device_id or sensor telemetry is present, otherwise API
    source_type = 'IOT_DEVICE' if device_id else 'API'

    # Validate coordinate completeness and numerical types
    latitude = None
    longitude = None
    if latitude_raw or longitude_raw:
        if not (latitude_raw and longitude_raw):
            return JsonResponse({
                'success': False,
                'error': 'Both latitude and longitude must be provided together for geographical positioning.'
            }, status=400)
        try:
            latitude = float(latitude_raw)
            if not (-90.0 <= latitude <= 90.0):
                return JsonResponse({
                    'success': False,
                    'error': 'Latitude must be between -90.0 and +90.0 degrees.'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': f'Invalid latitude value "{latitude_raw}". Must be a valid float.'
            }, status=400)

        try:
            longitude = float(longitude_raw)
            if not (-180.0 <= longitude <= 180.0):
                return JsonResponse({
                    'success': False,
                    'error': 'Longitude must be between -180.0 and +180.0 degrees.'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': f'Invalid longitude value "{longitude_raw}". Must be a valid float.'
            }, status=400)

    temperature = None
    if temperature_raw:
        try:
            temperature = float(temperature_raw)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': f'Invalid temperature value "{temperature_raw}". Must be a valid float.'
            }, status=400)

    humidity = None
    if humidity_raw:
        try:
            humidity = float(humidity_raw)
            if not (0.0 <= humidity <= 100.0):
                return JsonResponse({
                    'success': False,
                    'error': 'Humidity must be a percentage between 0.0 and 100.0.'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': f'Invalid humidity value "{humidity_raw}". Must be a valid float.'
            }, status=400)

    try:
        record = process_image_prediction(
            image_file,
            notes=notes,
            user=user,
            source_type=source_type,
            device_id=device_id,
            latitude=latitude,
            longitude=longitude,
            temperature=temperature,
            humidity=humidity,
        )

        response_data = {
            "success": True,
            "prediction": record.predicted_class,
            "confidence": round(record.confidence, 4),
            "probabilities": {
                "Low_to_Medium_Rain": round(record.low_to_medium_probability, 4),
                "Medium_to_Heavy_Rain": round(record.medium_to_heavy_probability, 4),
                "No_to_Low_Rain": round(record.no_to_low_probability, 4),
            },
            "timestamp": record.created_at.isoformat() if record.created_at else None,
            "model_version": record.model_version,
            "id": str(record.id),
            "predicted_class": record.predicted_class,
            "processing_time_ms": round(record.processing_time, 2),
            "source_type": record.source_type,
            "device_id": record.device_id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "temperature": record.temperature,
            "humidity": record.humidity,
        }
        return JsonResponse(response_data, status=200)
    except (InvalidImageFormatError, CorruptedImageError, FileTooLargeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except InferenceError as e:
        logger.error(f"Inference error in API endpoint: {e}")
        return JsonResponse({'success': False, 'error': 'AI inference service error occurred. Please try again.'}, status=500)
    except Exception:
        logger.exception("Unexpected error in API predict view")
        return JsonResponse({'success': False, 'error': 'An internal server error occurred while processing image. Please try again.'}, status=500)


def demo_view(request):
    """
    Dedicated live demonstration mode optimized for projector presentations.
    Displays curated sample cloud specimens, live image stage preview,
    and instantaneous AI inference execution with rich telemetry.
    """
    repo_root = Path(settings.BASE_DIR).parent
    demo_dir = repo_root / "demo_images"
    labels_file = demo_dir / "labels.json"

    samples = []
    if demo_dir.exists() and labels_file.exists():
        try:
            with open(labels_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for item in manifest.get("samples", []):
                rel_p = item.get("relative_path", "")
                cat_key = item.get("category_key", "low_medium")
                fn = item.get("filename", "")
                samples.append({
                    "filename": fn,
                    "relative_path": rel_p,
                    "serve_url": f"/demo/image/{cat_key}/{fn}",
                    "category_key": cat_key,
                    "category_code": item.get("category_code", ""),
                    "category_label": item.get("category_label", ""),
                    "cloud_genus": item.get("cloud_genus", "Cloud Specimen"),
                    "resolution": item.get("resolution", "400x400"),
                    "size_bytes": item.get("size_bytes", 0),
                    "is_sample_dataset_image": True,
                })
        except Exception as e:
            logger.warning(f"Error reading demo labels: {e}")

    # Fallback if demo_images was not prepared yet
    if not samples:
        for cat in ["Low_to_Medium_Rain", "Medium_to_Heavy_Rain", "No_to_Low_Rain"]:
            cat_dir = settings.AI_MODEL_DIR / "datasets" / "splits" / "test" / cat
            if cat_dir.exists():
                for img_p in sorted(cat_dir.glob("*.jpg"))[:4]:
                    samples.append({
                        "filename": img_p.name,
                        "relative_path": f"03_AI_Model/datasets/splits/test/{cat}/{img_p.name}",
                        "serve_url": "",
                        "category_key": cat.lower(),
                        "category_code": cat,
                        "category_label": cat.replace("_", " "),
                        "cloud_genus": "Verified Dataset Specimen",
                        "resolution": "400x400",
                        "size_bytes": img_p.stat().st_size,
                        "is_sample_dataset_image": True,
                    })

    return render(request, "predictions/demo.html", {
        "demo_samples": samples,
        "first_sample": samples[0] if samples else None,
        "page_title": "SKYsense AI - Live Demonstration Mode",
    })


def demo_image_serve_view(request, subpath):
    """
    Safely serves demo cloud photographs for live demonstration display.
    Guarded against path traversal.
    """
    repo_root = Path(settings.BASE_DIR).parent
    demo_root = (repo_root / "demo_images").resolve()
    requested_path = (demo_root / subpath).resolve()

    if not requested_path.is_relative_to(demo_root) or not requested_path.is_file():
        raise Http404("Demo image not found or unauthorized path.")

    return FileResponse(open(requested_path, "rb"), content_type="image/jpeg")


@require_POST
def demo_analyze_view(request):
    """
    Executes live AI inference for the demonstration mode.
    Accepts either:
    1. 'sample_path': path relative to repo root within demo_images/
    2. 'image': uploaded user file via multipart/form-data
    Returns real inference predictions, confidence, probabilities, latency, and scientific advisories.
    NO FAKE PREDICTIONS: calls the real deep learning model.
    """
    sample_path_str = request.POST.get("sample_path", "").strip()
    image_file = request.FILES.get("image")

    repo_root = Path(settings.BASE_DIR).parent
    image_bytes = None
    specimen_name = "User Uploaded Specimen"
    cloud_genus = "Custom Cloud Photograph"

    if image_file:
        # User uploaded their own image
        ext = Path(image_file.name).suffix.lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return JsonResponse({
                "success": False,
                "error": f"Unsupported format '{ext}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            }, status=400)
        if image_file.size > settings.MAX_UPLOAD_SIZE:
            return JsonResponse({
                "success": False,
                "error": "File size exceeds the 15 MB limit."
            }, status=400)
        # Deep Pillow verify
        try:
            image_file.seek(0)
            with Image.open(image_file) as im:
                im.verify()
                if im.format not in ['JPEG', 'PNG']:
                    return JsonResponse({"success": False, "error": f"Image format '{im.format}' not supported."}, status=400)
            image_file.seek(0)
            image_bytes = image_file.read()
            specimen_name = image_file.name
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Corrupted or invalid image: {e}"}, status=400)

    elif sample_path_str:
        # Sample dataset specimen from demo_images
        resolved_path = (repo_root / sample_path_str).resolve()
        demo_root = (repo_root / "demo_images").resolve()
        test_root = (settings.AI_MODEL_DIR / "datasets" / "splits" / "test").resolve()

        if not (resolved_path.is_relative_to(demo_root) or resolved_path.is_relative_to(test_root)):
            return JsonResponse({"success": False, "error": "Access denied: Unauthorized specimen path."}, status=403)

        if not resolved_path.exists() or not resolved_path.is_file():
            return JsonResponse({"success": False, "error": "Specimen file not found on disk."}, status=404)

        try:
            with open(resolved_path, "rb") as f:
                image_bytes = f.read()
            specimen_name = resolved_path.name
            genus_prefix = specimen_name.split("_")[0] if "_" in specimen_name else ""
            genus_dict = {
                "As": "Altostratus (As)", "Ns": "Nimbostratus (Ns)", "St": "Stratus (St)",
                "Sc": "Stratocumulus (Sc)", "Cb": "Cumulonimbus (Cb)", "Cu": "Cumulus (Cu)",
                "Ci": "Cirrus (Ci)", "Cc": "Cirrocumulus (Cc)", "Cs": "Cirrostratus (Cs)", "Ac": "Altocumulus (Ac)"
            }
            cloud_genus = genus_dict.get(genus_prefix, f"{genus_prefix} Cloud")
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Failed reading specimen: {e}"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "No image specimen or uploaded file provided."}, status=400)

    # Execute REAL AI Inference
    try:
        from src.inference import RainfallInferenceService, InferenceError
    except ImportError:
        return JsonResponse({"success": False, "error": "AI Inference engine is unavailable."}, status=500)

    try:
        service = RainfallInferenceService.get_instance()
        import time
        t_start = time.perf_counter()
        raw_result = service.predict(image_bytes)
        latency_ms = (time.perf_counter() - t_start) * 1000.0

        pred_class = raw_result["predicted_class"]
        confidence = raw_result["confidence"]
        probabilities = raw_result["probabilities"]

        advisory = METEOROLOGICAL_ADVISORIES.get(pred_class, {
            "context": "Cloud image analyzed.",
            "range": "Variable",
            "risk": "Moderate",
            "action": "Check local weather advisories."
        })

        label_map = {
            "Low_to_Medium_Rain": "Low to Medium Rain",
            "Medium_to_Heavy_Rain": "Medium to Heavy Rain",
            "No_to_Low_Rain": "No to Low Rain",
        }
        display_label = label_map.get(pred_class, pred_class.replace("_", " "))

        return JsonResponse({
            "success": True,
            "specimen_name": specimen_name,
            "cloud_genus": cloud_genus,
            "prediction": pred_class,
            "predicted_label": display_label,
            "confidence": round(confidence, 4),
            "confidence_pct": f"{confidence * 100:.1f}%",
            "probabilities": {
                "Low_to_Medium_Rain": round(probabilities.get("Low_to_Medium_Rain", 0.0), 4),
                "Medium_to_Heavy_Rain": round(probabilities.get("Medium_to_Heavy_Rain", 0.0), 4),
                "No_to_Low_Rain": round(probabilities.get("No_to_Low_Rain", 0.0), 4),
            },
            "processing_time_ms": round(latency_ms, 1),
            "model_version": "Xception-v1.0 (Deep Transfer CNN)",
            "explanation": {
                "risk_level": advisory["risk"],
                "rain_probability_range": advisory["range"],
                "meteorological_context": advisory["context"],
                "advisory_action": advisory["action"],
            }
        })
    except Exception as e:
        logger.exception("Error executing demo inference")
        return JsonResponse({"success": False, "error": f"Inference execution failed: {str(e)}"}, status=500)
