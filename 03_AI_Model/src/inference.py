"""
SKYsense AI - Production Inference Service
Provides a clean, standalone inference engine for cloud-image rainfall prediction.
Designed for high-throughput production deployment (Django, APIs, background workers, CLI).

Features:
- Singleton / Lazy model loading (loaded once in memory, reused across requests)
- Strict image validation (format, size limits, stream integrity)
- Rejection of corrupted, oversized, or unsupported files
- Deterministic 256x256 RGB normalization [0.0, 1.0]
- Verified alphabetical label mapping (0: Low_to_Medium_Rain, 1: Medium_to_Heavy_Rain, 2: No_to_Low_Rain)
- No dependency on Django or notebook environment
"""

import os
from pathlib import Path
from typing import Dict, Any, Union, Optional
import numpy as np
from PIL import Image, UnidentifiedImageError

try:
    from . import config
except ImportError:
    import config


# =====================================================================
# Custom Domain Exceptions
# =====================================================================

class InferenceError(Exception):
    """Base exception for inference operations."""
    pass


class InvalidImageFormatError(InferenceError):
    """Raised when an unsupported image format is provided."""
    pass


class CorruptedImageError(InferenceError):
    """Raised when an image file cannot be decoded or is damaged."""
    pass


class FileTooLargeError(InferenceError):
    """Raised when an image exceeds maximum allowed payload size."""
    pass


class ModelNotFoundError(InferenceError):
    """Raised when the serialized model file is missing."""
    pass


# =====================================================================
# Constants & Constraints
# =====================================================================

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_PIL_FORMATS = {"JPEG", "PNG"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MAX_IMAGE_DIMENSION = 8192  # Prevent decompression bomb attacks
TARGET_SIZE = (256, 256)
NORM_FACTOR = 1.0 / 255.0

# Verified Alphabetical Class Mapping
CLASS_NAMES = [
    "Low_to_Medium_Rain",
    "Medium_to_Heavy_Rain",
    "No_to_Low_Rain",
]

CLASS_TO_IDX = {
    "Low_to_Medium_Rain": 0,
    "Medium_to_Heavy_Rain": 1,
    "No_to_Low_Rain": 2,
}

IDX_TO_CLASS = {0: "Low_to_Medium_Rain", 1: "Medium_to_Heavy_Rain", 2: "No_to_Low_Rain"}


# =====================================================================
# Production Inference Engine
# =====================================================================

class RainfallInferenceService:
    """
    Thread-safe, lazy-loading production inference service.
    Loads the trained model once upon first request and maintains it in memory.
    """

    _instance: Optional["RainfallInferenceService"] = None
    _model = None
    _model_path: Optional[Path] = None

    def __init__(self, model_path: Optional[Union[str, Path]] = None):
        """
        Initializes the service with an optional explicit model path.
        If not supplied, automatically resolves to best_xception_rainfall.keras.
        """
        if model_path is not None:
            self.model_path = Path(model_path)
        elif config.BEST_MODEL_PATH.exists():
            self.model_path = config.BEST_MODEL_PATH
        elif config.FINAL_MODEL_PATH.exists():
            self.model_path = config.FINAL_MODEL_PATH
        elif config.TFLITE_MODEL_PATH.exists():
            self.model_path = config.TFLITE_MODEL_PATH
        else:
            raise ModelNotFoundError(
                f"No trained model found in {config.MODELS_DIR}. "
                "Ensure baseline model training or export has been executed."
            )

    @classmethod
    def get_instance(cls, model_path: Optional[Union[str, Path]] = None) -> "RainfallInferenceService":
        """Singleton accessor ensuring only one instance and model exists in memory."""
        if cls._instance is None:
            cls._instance = cls(model_path=model_path)
        return cls._instance

    def _load_model_if_needed(self):
        """Loads model into memory if not already cached."""
        if self._model is not None:
            return

        if not self.model_path.exists():
            raise ModelNotFoundError(f"Model file not found at: {self.model_path}")

        # Lazy import of tensorflow so modules importing inference.py don't pay startup cost upfront
        import tensorflow as tf

        is_tflite = self.model_path.suffix.lower() == ".tflite"
        if is_tflite:
            interpreter = tf.lite.Interpreter(model_path=str(self.model_path))
            interpreter.allocate_tensors()
            self._model = {
                "type": "tflite",
                "interpreter": interpreter,
                "input_details": interpreter.get_input_details(),
                "output_details": interpreter.get_output_details(),
            }
        else:
            keras_model = tf.keras.models.load_model(str(self.model_path))
            self._model = {
                "type": "keras",
                "model": keras_model,
            }

    def validate_and_load_image(self, image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """
        Validates the input image against file constraints and corruption.
        Rejects:
        - Non-existent files
        - Unsupported file extensions
        - Files exceeding size threshold
        - Corrupted or truncated image streams
        - Decompression bombs
        """
        if isinstance(image_input, (str, Path)):
            file_path = Path(image_input)
            if not file_path.exists():
                raise FileNotFoundError(f"Image file does not exist: {file_path}")

            # Check file extension
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise InvalidImageFormatError(
                    f"Unsupported image extension '{file_path.suffix}'. "
                    f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                )

            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                raise CorruptedImageError(f"Image file is empty (0 bytes): {file_path}")
            if file_size > MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
                raise FileTooLargeError(
                    f"Image file size ({size_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.0f} MB)."
                )

            # Integrity verification
            try:
                with Image.open(file_path) as test_img:
                    test_img.verify()
            except Exception as e:
                raise CorruptedImageError(f"Image integrity verification failed: {e}")

            # Open image for pixel decoding
            try:
                img = Image.open(file_path)
                img.load()  # Force reading pixel data to catch truncated files
            except Exception as e:
                raise CorruptedImageError(f"Failed to decode image data: {e}")

        elif isinstance(image_input, bytes):
            import io
            if len(image_input) == 0:
                raise CorruptedImageError("Image byte stream is empty.")
            if len(image_input) > MAX_FILE_SIZE_BYTES:
                raise FileTooLargeError("In-memory image byte payload exceeds maximum allowed size.")

            try:
                stream = io.BytesIO(image_input)
                with Image.open(stream) as test_img:
                    test_img.verify()
                stream.seek(0)
                img = Image.open(stream)
                img.load()
            except Exception as e:
                raise CorruptedImageError(f"Failed to decode in-memory image bytes: {e}")

        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise InvalidImageFormatError(
                f"Unsupported image input type: {type(image_input)}. Expected filepath, bytes, or PIL.Image."
            )

        # Validate PIL detected format
        if hasattr(img, "format") and img.format and img.format.upper() not in SUPPORTED_PIL_FORMATS:
            raise InvalidImageFormatError(
                f"Detected image format '{img.format}' is not supported. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_PIL_FORMATS))}"
            )

        # Prevent decompression bomb attacks
        width, height = img.size
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise FileTooLargeError(
                f"Image dimensions ({width}x{height}) exceed maximum allowed dimension ({MAX_IMAGE_DIMENSION}px)."
            )

        return img

    def preprocess(self, img: Image.Image) -> np.ndarray:
        """
        Transforms validated PIL Image into model input tensor:
        1. Convert to RGB (drops alpha / converts grayscale)
        2. Resize to 256x256 using bilinear interpolation
        3. Convert to float32 numpy array
        4. Normalize pixels to [0.0, 1.0]
        5. Add batch dimension -> (1, 256, 256, 3)
        """
        rgb_img = img.convert("RGB")
        resized_img = rgb_img.resize(TARGET_SIZE, Image.Resampling.BILINEAR)
        img_array = np.array(resized_img, dtype=np.float32)
        normalized_array = img_array * NORM_FACTOR
        batch_tensor = np.expand_dims(normalized_array, axis=0)
        return batch_tensor

    def predict(self, image_input: Union[str, Path, bytes, Image.Image]) -> Dict[str, Any]:
        """
        Executes end-to-end inference on the input image.

        Returns structured dict matching project specification:
        {
            "predicted_class": "...",
            "confidence": 0.xxxx,
            "probabilities": {
                "Low_to_Medium_Rain": 0.xxxx,
                "Medium_to_Heavy_Rain": 0.xxxx,
                "No_to_Low_Rain": 0.xxxx
            }
        }
        """
        # 1. Validate and load image
        img = self.validate_and_load_image(image_input)

        # 2. Preprocess to normalized tensor
        tensor = self.preprocess(img)

        # 3. Ensure model is loaded into memory
        self._load_model_if_needed()

        # 4. Run prediction
        if self._model["type"] == "tflite":
            interpreter = self._model["interpreter"]
            input_idx = self._model["input_details"][0]["index"]
            output_idx = self._model["output_details"][0]["index"]
            interpreter.set_tensor(input_idx, tensor)
            interpreter.invoke()
            raw_probs = interpreter.get_tensor(output_idx)[0]
        else:
            keras_model = self._model["model"]
            raw_probs = keras_model.predict(tensor, verbose=0)[0]

        # 5. Extract probabilities matching verified alphabetical mapping
        pred_idx = int(np.argmax(raw_probs))
        predicted_class = IDX_TO_CLASS[pred_idx]
        confidence = float(raw_probs[pred_idx])

        probabilities = {
            cls_name: round(float(raw_probs[CLASS_TO_IDX[cls_name]]), 4)
            for cls_name in CLASS_NAMES
        }

        # 6. Structured Output
        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": probabilities,
        }


# Global convenience function
def predict_image(image_input: Union[str, Path, bytes, Image.Image], model_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Convenience function for stateless one-off or server inference.
    Reuses the singleton inference engine.
    """
    service = RainfallInferenceService.get_instance(model_path=model_path)
    return service.predict(image_input)
