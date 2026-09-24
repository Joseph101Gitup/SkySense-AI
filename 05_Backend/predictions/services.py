"""
Service layer bridging Django with the standalone AI inference module (03_AI_Model.src.inference).
Adheres strictly to the requirement: NO AI PREDICTION LOGIC IS DUPLICATED IN DJANGO.
"""

import sys
import json
import logging
from pathlib import Path
from django.conf import settings
from .models import PredictionRecord

logger = logging.getLogger(__name__)

# Ensure 03_AI_Model is on sys.path
AI_MODEL_DIR = settings.AI_MODEL_DIR
if str(AI_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODEL_DIR))

# Import directly from the standalone inference module
try:
    from src.inference import (
        RainfallInferenceService,
        InferenceError,
        InvalidImageFormatError,
        CorruptedImageError,
        FileTooLargeError,
    )
except ImportError as e:
    logger.error(f"Failed to import RainfallInferenceService from {AI_MODEL_DIR}: {e}")
    RainfallInferenceService = None
    InferenceError = Exception
    InvalidImageFormatError = Exception
    CorruptedImageError = Exception
    FileTooLargeError = Exception


METEOROLOGICAL_ADVISORIES = {
    "Low_to_Medium_Rain": {
        "context": "Extensive layered clouds detected (e.g., Altostratus, Stratocumulus, Nimbostratus).",
        "range": "40% - 75%",
        "risk": "Moderate",
        "action": "Steady drizzle or light-to-moderate rain expected. Postpone sensitive open-air operations.",
    },
    "Medium_to_Heavy_Rain": {
        "context": "Deep, vertically developed convective clouds detected (e.g., Cumulonimbus, Cumulus congestus).",
        "range": "> 85%",
        "risk": "High",
        "action": "High likelihood of torrential downpours or thunderstorms. Secure sensitive outdoor assets immediately.",
    },
    "No_to_Low_Rain": {
        "context": "High-altitude or thin patchy cloud formations detected (e.g., Cirrus, Cirrocumulus, Altocumulus).",
        "range": "< 15%",
        "risk": "Low",
        "action": "Normal dry conditions. Safe to proceed with outdoor activities, transport, and agricultural work.",
    }
}


def process_image_prediction(
    uploaded_file,
    notes: str = "",
    user=None,
    source_type: str = 'WEB_UPLOAD',
    device_id: str = None,
    latitude: float = None,
    longitude: float = None,
    temperature: float = None,
    humidity: float = None,
) -> PredictionRecord:
    """
    Delegates image processing to the standalone AI inference service,
    persists the prediction record in the SQLite database, and returns the model instance.
    Supports optional edge IoT telemetry fields.
    """
    if RainfallInferenceService is None:
        raise InferenceError("AI Inference Service is not available. Please verify model environment.")

    # 1. Acquire singleton inference service instance
    service = RainfallInferenceService.get_instance()

    # 2. Read bytes and execute inference with precise latency tracking
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # Reset pointer for Django ImageField storage

    import time
    start_time = time.perf_counter()
    raw_result = service.predict(file_bytes)
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    predicted_class = raw_result["predicted_class"]
    confidence = raw_result["confidence"]
    probabilities = raw_result["probabilities"]

    advisory_info = METEOROLOGICAL_ADVISORIES.get(predicted_class, {
        "context": "Cloud image analyzed.",
        "range": "Variable",
        "risk": "Moderate",
        "action": "Check local meteorological updates.",
    })

    # 3. Create persistent record in database with explicit validation
    record = PredictionRecord(
        user=user,
        image=uploaded_file,
        original_filename=uploaded_file.name,
        predicted_class=predicted_class,
        confidence=confidence,
        low_to_medium_probability=probabilities.get("Low_to_Medium_Rain", 0.0),
        medium_to_heavy_probability=probabilities.get("Medium_to_Heavy_Rain", 0.0),
        no_to_low_probability=probabilities.get("No_to_Low_Rain", 0.0),
        processing_time=round(latency_ms, 2),
        model_version='Xception-v1.0',
        source_type=source_type,
        device_id=device_id,
        latitude=latitude,
        longitude=longitude,
        temperature=temperature,
        humidity=humidity,
        risk_level=advisory_info["risk"],
        rain_probability_range=advisory_info["range"],
        meteorological_context=advisory_info["context"],
        advisory_action=advisory_info["action"],
        user_notes=notes,
    )
    record.save()
    return record


def get_sample_test_images():
    """
    Retrieves representative sample cloud images for one-click web demonstration.
    Prioritizes the curated demo_images/ directory with ground-truth source labels,
    with fallback to test partition splits.
    """
    repo_root = settings.BASE_DIR.parent
    demo_dir = repo_root / "demo_images"
    labels_file = demo_dir / "labels.json"
    samples = []

    # 1. Primary: Load curated demo_images specimens with labels metadata
    if demo_dir.exists() and labels_file.exists():
        try:
            with open(labels_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            # Group by category to pick diverse representative specimens
            cat_groups = {}
            for item in manifest.get("samples", []):
                cat = item.get("category_code")
                cat_groups.setdefault(cat, []).append(item)

            # Select up to 2 specimens per category (6 total) for balanced display
            for cat, items in cat_groups.items():
                for item in items[:2]:
                    rel_p = item.get("relative_path", "")
                    full_p = (repo_root / rel_p).resolve()
                    if full_p.exists() and full_p.is_file():
                        samples.append({
                            "category": cat,
                            "display_name": item.get("category_label", cat),
                            "cloud_genus": item.get("cloud_genus", "Sample Cloud"),
                            "path": str(full_p),
                            "filename": item.get("filename", full_p.name),
                            "resolution": item.get("resolution", "400x400"),
                            "is_sample_dataset_image": True,
                        })
            if samples:
                return samples
        except Exception as e:
            logger.warning(f"Error loading demo_images manifest: {e}")

    # 2. Fallback: Directly sample from 03_AI_Model/datasets/splits/test/
    test_splits_dir = settings.AI_MODEL_DIR / "datasets" / "splits" / "test"
    if test_splits_dir.exists():
        for category in ["Low_to_Medium_Rain", "Medium_to_Heavy_Rain", "No_to_Low_Rain"]:
            cat_dir = test_splits_dir / category
            if cat_dir.exists():
                for img in sorted(cat_dir.glob("*.jpg"))[:2]:
                    samples.append({
                        "category": category,
                        "display_name": category.replace("_", " "),
                        "cloud_genus": "Verified Dataset Specimen",
                        "path": str(img.resolve()),
                        "filename": img.name,
                        "resolution": "400x400",
                        "is_sample_dataset_image": True,
                    })
    return samples
