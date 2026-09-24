#!/usr/bin/env python
"""
SKYsense AI - Model Training Automation Script
Executes two-phase transfer learning using Xception backbone:
Phase 1: Frozen backbone feature extraction
Phase 2: Fine-tuning with learning rate scheduling and early stopping
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"

if str(AI_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODEL_DIR))

try:
    from src import config, train
except ImportError as e:
    print(f"[!] Import error: {e}. Please ensure 03_AI_Model dependencies are installed.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Train Deep Learning Model")
    parser.add_argument("--phase1-epochs", type=int, default=config.PHASE1_EPOCHS,
                        help=f"Phase 1 epochs (frozen backbone). Default: {config.PHASE1_EPOCHS}")
    parser.add_argument("--phase2-epochs", type=int, default=config.PHASE2_EPOCHS,
                        help=f"Phase 2 epochs (fine-tuning). Default: {config.PHASE2_EPOCHS}")
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE,
                        help=f"Training batch size. Default: {config.BATCH_SIZE}")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fast 1-epoch smoke test to verify training pipeline machinery")
    args = parser.parse_args()

    phase1 = 1 if args.dry_run else args.phase1_epochs
    phase2 = 1 if args.dry_run else args.phase2_epochs

    print("=" * 65)
    print("       SKYsense AI - Model Training Pipeline")
    print("=" * 65)
    print(f"  Backbone Architecture : Xception (ImageNet pre-trained)")
    print(f"  Phase 1 Epochs        : {phase1}")
    print(f"  Phase 2 Epochs        : {phase2}")
    print(f"  Batch Size            : {args.batch_size}")
    print(f"  Target Classes        : {', '.join(config.CLASS_NAMES)}")
    print(f"  Artifact Directory    : {config.MODELS_DIR}")
    print("=" * 65 + "\n")

    try:
        summary = train.run_training(
            phase1_epochs=phase1,
            phase2_epochs=phase2,
            batch_size=args.batch_size
        )
        print("\n" + "=" * 65)
        print("  [SUCCESS] Model training completed successfully.")
        print(f"  Best Model Saved To   : {config.BEST_MODEL_PATH}")
        print(f"  Final Model Saved To  : {config.FINAL_MODEL_PATH}")
        print("=" * 65)
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Training execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
