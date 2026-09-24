"""
Database Model Definition for SKYsense AI.
Defines the primary Prediction entity with rigorous validation, database indexing,
and forward-compatible optional IoT edge telemetry attributes.
"""

import os
import re
import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def safe_prediction_image_path(instance, filename):
    """
    Generate a secure, randomized file path for uploaded images to prevent:
    - Path traversal attacks (e.g., ../../etc/passwd)
    - File collision / overwrites
    - Execution of malicious scripts via double extensions or dangerous names
    Format: predictions/%Y/%m/%d/<uuid4_hex>.<extension>
    """
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png'])
    if ext not in allowed_exts:
        ext = '.jpg'
    safe_name = f"{uuid.uuid4().hex}{ext}"
    date_path = timezone.now().strftime('predictions/%Y/%m/%d')
    return f"{date_path}/{safe_name}"


class SourceType(models.TextChoices):
    WEB_UPLOAD = 'WEB_UPLOAD', 'Web Upload'
    IOT_DEVICE = 'IOT_DEVICE', 'IoT Device'
    API = 'API', 'API'


class RainfallClass(models.TextChoices):
    LOW_TO_MEDIUM = 'Low_to_Medium_Rain', 'Low to Medium Rain'
    MEDIUM_TO_HEAVY = 'Medium_to_Heavy_Rain', 'Medium to Heavy Rain'
    NO_TO_LOW = 'No_to_Low_Rain', 'No to Low Rain'


class Prediction(models.Model):
    """
    Primary persistent entity storing inference results and meteorological context
    derived from sky-facing cloud imagery.
    """

    # --- Core Identification & Ingestion ---
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique UUID identifier for this prediction record."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='predictions',
        db_index=True,
        help_text="User/Researcher who submitted this prediction."
    )
    image = models.ImageField(
        upload_to=safe_prediction_image_path,
        help_text="Uploaded or ingested sky cloud specimen image."
    )
    original_filename = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Original filename of the ingested specimen."
    )

    # --- Inference Results ---
    predicted_class = models.CharField(
        max_length=64,
        choices=RainfallClass.choices,
        db_index=True,
        help_text="Dominant precipitation category predicted by the CNN."
    )
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        db_index=True,
        help_text="Model confidence score between 0.0 and 1.0 for the predicted class."
    )
    low_to_medium_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Softmax probability for Low_to_Medium_Rain (Class 0)."
    )
    medium_to_heavy_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Softmax probability for Medium_to_Heavy_Rain (Class 1)."
    )
    no_to_low_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Softmax probability for No_to_Low_Rain (Class 2)."
    )

    # --- Performance & Provenance ---
    processing_time = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text="Inference execution latency in milliseconds."
    )
    model_version = models.CharField(
        max_length=64,
        default='Xception-v1.0',
        db_index=True,
        help_text="Deep learning backbone architecture and checkpoint release tag."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="UTC timestamp when prediction was recorded."
    )

    # --- Optional IoT Integration Fields (Pre-wired for Future Edge Nodes) ---
    source_type = models.CharField(
        max_length=32,
        choices=SourceType.choices,
        default=SourceType.WEB_UPLOAD,
        db_index=True,
        help_text="Ingestion channel (Currently default: WEB_UPLOAD. IOT_DEVICE/API available for future hardware)."
    )
    device_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text="Optional edge device hardware identifier (e.g. Raspberry Pi / ESP32 node)."
    )
    latitude = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Geographical latitude coordinate of capture (-90.0 to +90.0)."
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Geographical longitude coordinate of capture (-180.0 to +180.0)."
    )
    temperature = models.FloatField(
        blank=True,
        null=True,
        help_text="Ambient ground temperature in °C captured by collocated IoT weather sensors."
    )
    humidity = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Relative humidity percentage (0.0 to 100.0%) captured by collocated IoT weather sensors."
    )

    # --- Meteorological Context & Qualitative Annotations ---
    risk_level = models.CharField(
        max_length=32,
        default='Moderate',
        help_text="Categorical precipitation severity level: Low, Moderate, High."
    )
    rain_probability_range = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text="Estimated empirical rainfall probability bracket (e.g. '> 85%')."
    )
    meteorological_context = models.TextField(
        blank=True,
        default='',
        help_text="Scientific explanation of identified cloud regimes (e.g. Stratus, Cumulonimbus)."
    )
    advisory_action = models.TextField(
        blank=True,
        default='',
        help_text="Operational recommendations for field operations, aviation, or agriculture."
    )
    user_notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional researcher observations or ground truth notes."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prediction'
        verbose_name_plural = 'Predictions'
        indexes = [
            models.Index(fields=['-created_at'], name='pred_created_idx'),
            models.Index(fields=['predicted_class'], name='pred_class_idx'),
            models.Index(fields=['source_type'], name='pred_source_idx'),
            models.Index(fields=['confidence'], name='pred_conf_idx'),
            models.Index(fields=['device_id'], name='pred_device_idx'),
            models.Index(fields=['model_version'], name='pred_model_ver_idx'),
            models.Index(fields=['user'], name='pred_user_idx'),
        ]

    def __str__(self):
        return f"{self.original_filename} -> {self.predicted_class} ({self.confidence_pct})"

    def clean(self):
        """
        Database and model-level validation:
        1. Probabilities must sum approximately to 1.0 (allowing for minor floating point rounding)
        2. If either latitude or longitude is provided, both must be supplied
        3. Predicted class should align with maximum probability
        """
        super().clean()

        # Validate probability sum
        if (self.low_to_medium_probability is not None and
            self.medium_to_heavy_probability is not None and
            self.no_to_low_probability is not None):
            total_prob = (
                self.low_to_medium_probability +
                self.medium_to_heavy_probability +
                self.no_to_low_probability
            )
            if not (0.95 <= total_prob <= 1.05):
                raise ValidationError({
                    'confidence': f"Class probabilities must sum approximately to 1.0 (current sum: {total_prob:.4f})."
                })

        # Validate coordinate pair completeness
        if (self.latitude is not None and self.longitude is None) or (self.latitude is None and self.longitude is not None):
            raise ValidationError({
                'latitude': "Both latitude and longitude must be provided together for geographical positioning."
            })

    def save(self, *args, **kwargs):
        # Sanitize original_filename to prevent stored XSS or control-character injection
        if self.original_filename:
            # Strip directory path and keep basename only
            cleaned_name = os.path.basename(str(self.original_filename))
            # Remove any dangerous characters (allow alphanumeric, space, dot, hyphen, underscore)
            cleaned_name = re.sub(r'[^\w\s\.-]', '', cleaned_name).strip()
            self.original_filename = cleaned_name[:255] or 'uploaded_specimen.jpg'
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('predictions:detail', kwargs={'pk': self.pk})

    # --- Backward-compatible & Template Convenience Properties ---

    @property
    def image_filename(self):
        return self.original_filename

    @image_filename.setter
    def image_filename(self, value):
        self.original_filename = value

    @property
    def prob_low_to_medium(self):
        return self.low_to_medium_probability

    @property
    def prob_medium_to_heavy(self):
        return self.medium_to_heavy_probability

    @property
    def prob_no_to_low(self):
        return self.no_to_low_probability

    @property
    def latency_ms(self):
        return round(self.processing_time, 1)

    @property
    def display_name(self):
        return self.predicted_class.replace('_', ' ')

    @property
    def confidence_pct(self):
        return round(self.confidence * 100, 1)

    @property
    def confidence_percent(self):
        return round(self.confidence * 100, 1)

    @property
    def prob_low_pct(self):
        return round(self.low_to_medium_probability * 100, 1)

    @property
    def prob_med_pct(self):
        return round(self.medium_to_heavy_probability * 100, 1)

    @property
    def prob_no_pct(self):
        return round(self.no_to_low_probability * 100, 1)

    @property
    def image_size_kb(self):
        try:
            return round(self.image.size / 1024, 1)
        except Exception:
            return 0.0

    @property
    def has_geo_coordinates(self):
        """Returns True if both latitude and longitude are specified."""
        return self.latitude is not None and self.longitude is not None

    @property
    def has_environmental_telemetry(self):
        """Returns True if either temperature or humidity sensor readings are specified."""
        return self.temperature is not None or self.humidity is not None

    @property
    def badge_color(self):
        mapping = {
            'No_to_Low_Rain': 'emerald',
            'Low_to_Medium_Rain': 'amber',
            'Medium_to_Heavy_Rain': 'rose',
        }
        return mapping.get(self.predicted_class, 'slate')

    def to_dict(self):
        """Returns JSON-serializable dictionary matching project specification."""
        return {
            "id": str(self.id),
            "original_filename": self.original_filename,
            "predicted_class": self.predicted_class,
            "confidence": round(self.confidence, 4),
            "probabilities": {
                "Low_to_Medium_Rain": round(self.low_to_medium_probability, 4),
                "Medium_to_Heavy_Rain": round(self.medium_to_heavy_probability, 4),
                "No_to_Low_Rain": round(self.no_to_low_probability, 4),
            },
            "processing_time_ms": round(self.processing_time, 2),
            "model_version": self.model_version,
            "source_type": self.source_type,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "risk_level": self.risk_level,
            "rain_probability_range": self.rain_probability_range,
            "meteorological_context": self.meteorological_context,
            "recommended_action": self.advisory_action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Model alias for backwards compatibility across existing views/services
PredictionRecord = Prediction
