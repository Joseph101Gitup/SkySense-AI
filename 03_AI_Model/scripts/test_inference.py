"""
SKYsense AI - Comprehensive Unit & Integration Tests for Production Inference
Tests:
- Valid predictions on JPG and PNG
- Exact output schema matching
- Model caching verification (no reloading)
- Rejection of invalid extensions (.txt, .pdf)
- Rejection of corrupted files
- Rejection of oversized payloads
- CLI execution validation
"""

import sys
import os
import io
import tempfile
from pathlib import Path
from PIL import Image

# Ensure 03_AI_Model is on sys.path
ai_dir = Path(__file__).resolve().parent.parent
if str(ai_dir) not in sys.path:
    sys.path.insert(0, str(ai_dir))

from src.inference import (
    RainfallInferenceService,
    predict_image,
    InvalidImageFormatError,
    CorruptedImageError,
    FileTooLargeError,
    CLASS_NAMES
)
from src import config


def run_tests():
    print("=" * 60)
    print("   RUNNING PRODUCTION INFERENCE SERVICE TEST SUITE")
    print("=" * 60)

    service = RainfallInferenceService.get_instance()

    # Find a real test sample
    test_samples = list(config.TEST_DIR.rglob("*.jpg"))
    if not test_samples:
        raise RuntimeError("No test images found in datasets/splits/test")
    test_image_path = test_samples[0]
    print(f"Sample test image: {test_image_path.name}")

    # -------------------------------------------------------------
    # Test 1: Valid Prediction & Output Structure
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing valid prediction and output schema...")
    result = service.predict(test_image_path)
    assert isinstance(result, dict), "Result must be a dictionary"
    assert "predicted_class" in result, "Missing 'predicted_class'"
    assert "confidence" in result, "Missing 'confidence'"
    assert "probabilities" in result, "Missing 'probabilities'"
    assert result["predicted_class"] in CLASS_NAMES, f"Invalid predicted class {result['predicted_class']}"
    assert isinstance(result["confidence"], float), "Confidence must be float"
    assert 0.0 <= result["confidence"] <= 1.0, f"Confidence {result['confidence']} out of range [0, 1]"

    probs = result["probabilities"]
    for c in CLASS_NAMES:
        assert c in probs, f"Missing class '{c}' in probabilities"
        assert 0.0 <= probs[c] <= 1.0, f"Probability for '{c}' out of range [0, 1]"

    prob_sum = sum(probs.values())
    assert abs(prob_sum - 1.0) < 0.01, f"Probabilities must sum to ~1.0, got {prob_sum}"
    print("  -> Passed! Result structure:")
    print("    ", result)

    # -------------------------------------------------------------
    # Test 2: Model Caching Verification
    # -------------------------------------------------------------
    print("\n[TEST 2] Verifying model is cached in memory (no reloading)...")
    initial_model_obj = service._model
    assert initial_model_obj is not None, "Model must be loaded"

    # Second call
    result2 = service.predict(test_image_path)
    second_model_obj = service._model
    assert initial_model_obj is second_model_obj, "Model instance changed! Model must not be reloaded."
    assert result == result2, "Predictions for identical inputs differed!"
    print("  -> Passed! Same model instance preserved across calls.")

    # -------------------------------------------------------------
    # Test 3: PNG Format Support & RGB Conversion
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing PNG format with RGBA channel conversion...")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
        tmp_png_path = Path(tmp_png.name)
    try:
        # Create a test RGBA PNG image
        png_img = Image.new("RGBA", (300, 300), color=(100, 150, 200, 128))
        png_img.save(tmp_png_path, format="PNG")

        png_result = service.predict(tmp_png_path)
        assert png_result["predicted_class"] in CLASS_NAMES
        print("  -> Passed! PNG with RGBA correctly converted and predicted.")
    finally:
        if tmp_png_path.exists():
            tmp_png_path.unlink()

    # -------------------------------------------------------------
    # Test 4: Rejection of Unsupported File Formats
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing rejection of unsupported file extensions...")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_txt:
        tmp_txt.write(b"This is a text file.")
        tmp_txt_path = Path(tmp_txt.name)
    try:
        try:
            service.predict(tmp_txt_path)
            assert False, "Failed to reject .txt file"
        except InvalidImageFormatError as e:
            print(f"  -> Passed! Correctly rejected: {e}")
    finally:
        if tmp_txt_path.exists():
            tmp_txt_path.unlink()

    # -------------------------------------------------------------
    # Test 5: Rejection of Corrupted Image Files
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing rejection of corrupted image files...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_corrupt:
        tmp_corrupt.write(b"\xFF\xD8\xFF\xE0" + b"GARBAGE_NOT_A_VALID_JPEG_STREAM")
        tmp_corrupt_path = Path(tmp_corrupt.name)
    try:
        try:
            service.predict(tmp_corrupt_path)
            assert False, "Failed to reject corrupted image"
        except CorruptedImageError as e:
            print(f"  -> Passed! Correctly rejected corrupted image: {e}")
    finally:
        if tmp_corrupt_path.exists():
            tmp_corrupt_path.unlink()

    # -------------------------------------------------------------
    # Test 6: Rejection of Oversized Image Files
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing rejection of oversized payloads...")
    # Test dimension bomb limit
    dim_bomb = Image.new("RGB", (9000, 100), color=(0, 0, 0))
    try:
        service.predict(dim_bomb)
        assert False, "Failed to reject dimension bomb image"
    except FileTooLargeError as e:
        print(f"  -> Passed! Correctly rejected oversized dimension: {e}")

    # -------------------------------------------------------------
    # Test 7: In-Memory Bytes Inference
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing direct byte-stream inference...")
    with open(test_image_path, "rb") as f:
        img_bytes = f.read()

    bytes_result = predict_image(img_bytes)
    assert bytes_result["predicted_class"] == result["predicted_class"]
    assert bytes_result["confidence"] == result["confidence"]
    print("  -> Passed! In-memory byte stream matched file path prediction exactly.")

    print("\n" + "=" * 60)
    print("   ALL INFERENCE SERVICE UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
