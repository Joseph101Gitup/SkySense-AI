#!/usr/bin/env python
"""
SKYsense AI - Model Evaluation Automation Script
Evaluates trained checkpoint on held-out test partition, computes Confusion Matrix,
Precision, Recall, F1-Scores, and updates the evaluation artifacts.
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"

if str(AI_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODEL_DIR))

try:
    from src import config, evaluate
except ImportError as e:
    print(f"[!] Import error: {e}. Please ensure 03_AI_Model dependencies are installed.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Evaluate Deep Learning Model")
    parser.add_argument("--model-path", type=str, default=str(config.BEST_MODEL_PATH),
                        help=f"Path to .keras model weights. Default: {config.BEST_MODEL_PATH}")
    parser.add_argument("--test-dir", type=str, default=str(config.TEST_DIR),
                        help=f"Path to test partition directory. Default: {config.TEST_DIR}")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    test_dir = Path(args.test_dir)

    print("=" * 65)
    print("       SKYsense AI - Test Set Model Evaluation")
    print("=" * 65)
    print(f"  Target Model Checkpoint : {model_path}")
    print(f"  Test Partition Path     : {test_dir}")
    print("=" * 65 + "\n")

    if not model_path.exists():
        print(f"[!] Error: Model weights file not found at: {model_path}")
        print("    Please train the model first using: python scripts/train_model.py")
        sys.exit(1)

    if not test_dir.exists():
        print(f"[!] Error: Test split directory not found at: {test_dir}")
        print("    Please verify dataset splits using: python scripts/verify_dataset.py")
        sys.exit(1)

    try:
        metrics = evaluate.evaluate_model(
            model_path=model_path
        )
        print("\n" + "=" * 65)
        print("  [SUCCESS] Evaluation completed successfully.")
        print(f"  Test Accuracy  : {metrics.get('test_accuracy', 0.0) * 100:.2f}%")
        print(f"  Test Loss      : {metrics.get('test_loss', 0.0):.4f}")
        print(f"  Macro F1-Score : {metrics.get('macro_avg_f1', 0.0) * 100:.2f}%")
        print(f"  Artifacts Path : {config.EVALUATION_DIR}")
        print("=" * 65)
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
