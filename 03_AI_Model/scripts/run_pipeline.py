"""
SKYsense AI - Master Pipeline Orchestrator
Executes the full pipeline sequentially:
  1. Dataset download & aggregation
  2. Stratified 70/15/15 disjoint splitting & verification
  3. Two-phase transfer learning training
  4. Independent test set evaluation & report generation
  5. Sample prediction verification
"""

import sys
import logging
from pathlib import Path

# Add src to path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import config
import dataset
import train
import evaluate
import predict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SKYsense_Pipeline")


def main():
    logger.info("=" * 65)
    logger.info("       STARTING SKYSENSE AI CLEAN BASELINE PIPELINE")
    logger.info("=" * 65)

    # 1. Dataset Preparation & Verification
    logger.info("\n>>> STEP 1: Dataset Verification & Stratified Splitting")
    src_dir = dataset.locate_or_download_ccsn()
    dataset.prepare_processed_dataset(src_dir)
    distribution = dataset.create_stratified_splits()
    logger.info(f"Verified dataset split: {distribution['summary']}")

    # 2. Train Model
    logger.info("\n>>> STEP 2: Training Xception Baseline (Two-Phase)")
    train_summary = train.run_training()
    logger.info(f"Training completed. Summary: {train_summary}")

    # 3. Independent Test Evaluation
    logger.info("\n>>> STEP 3: Independent Test Set Evaluation")
    eval_summary = evaluate.evaluate_model()
    logger.info(f"Test Accuracy: {eval_summary['test_accuracy'] * 100:.2f}% | Test Loss: {eval_summary['test_loss']:.4f}")

    # 4. Verification Prediction
    logger.info("\n>>> STEP 4: Sample Prediction Verification")
    predictor = predict.RainfallPredictor()
    test_files = list(config.TEST_DIR.rglob("*.jpg")) + list(config.TEST_DIR.rglob("*.png"))
    if test_files:
        sample_img = test_files[0]
        result = predictor.predict(sample_img)
        logger.info(f"Sample Image: {sample_img.name}")
        logger.info(f"Prediction: {result['predicted_class']} ({result['confidence_percentage']:.2f}% confidence)")
        logger.info(f"Probabilities: {result['class_probabilities']}")
        logger.info(f"Advisory: {result['recommended_action']}")

    logger.info("\n" + "=" * 65)
    logger.info("       SKYSENSE AI BASELINE PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
