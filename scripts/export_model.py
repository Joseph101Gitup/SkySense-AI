#!/usr/bin/env python
"""
SKYsense AI - Model Export Automation Script
Exports trained Keras model to TensorFlow Lite (.tflite) for edge, IoT, and mobile runtime.
Validates the exported binary by loading it into the TFLite Interpreter and verifying tensor I/O.
"""

import sys
import argparse
from pathlib import Path
import tensorflow as tf

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"

if str(AI_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODEL_DIR))

try:
    from src import config, model as model_module
except ImportError as e:
    print(f"[!] Import error: {e}. Please ensure 03_AI_Model dependencies are installed.")
    sys.exit(1)


def export_model(keras_model_path: Path, output_tflite_path: Path) -> bool:
    print("=" * 65)
    print("       SKYsense AI - Model Export to TensorFlow Lite")
    print("=" * 65)
    print(f"  Source Keras Model : {keras_model_path}")
    print(f"  Target TFLite Path : {output_tflite_path}")
    print("=" * 65 + "\n")

    if not keras_model_path.exists():
        print(f"[!] Error: Source model not found at {keras_model_path}")
        return False

    print("[+] Loading trained Keras model...")
    model = tf.keras.models.load_model(str(keras_model_path))

    print("[+] Converting model to optimized TFLite binary...")
    output_tflite_path.parent.mkdir(parents=True, exist_ok=True)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_bytes = converter.convert()

    with open(output_tflite_path, "wb") as f:
        f.write(tflite_bytes)

    size_mb = output_tflite_path.stat().st_size / (1024 * 1024)
    print(f"    [OK] TFLite file written successfully: {output_tflite_path} ({size_mb:.2f} MB)")

    print("[+] Validating TFLite binary with Interpreter...")
    try:
        interpreter = tf.lite.Interpreter(model_path=str(output_tflite_path))
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print(f"    [OK] Input Tensor Shape  : {input_details[0]['shape']} (dtype: {input_details[0]['dtype'].__name__})")
        print(f"    [OK] Output Tensor Shape : {output_details[0]['shape']} (dtype: {output_details[0]['dtype'].__name__})")
        print("\n" + "=" * 65)
        print("  [SUCCESS] Model export and validation PASSED.")
        print("=" * 65)
        return True
    except Exception as e:
        print(f"    [!] Interpreter validation error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Export Model to TFLite")
    parser.add_argument("--source", type=str, default=str(config.BEST_MODEL_PATH),
                        help=f"Source .keras model path. Default: {config.BEST_MODEL_PATH}")
    parser.add_argument("--output", type=str, default=str(config.TFLITE_MODEL_PATH),
                        help=f"Output .tflite path. Default: {config.TFLITE_MODEL_PATH}")
    args = parser.parse_args()

    success = export_model(Path(args.source), Path(args.output))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
