"""
SKYsense AI - Two-Phase Transfer Learning Training Pipeline
Executes frozen-backbone feature extraction (Phase 1) followed by fine-tuning (Phase 2),
with checkpointing, learning rate scheduling, early stopping, and history recording.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau,
    CSVLogger
)

try:
    from . import config
    from . import dataset
    from . import model as model_module
except ImportError:
    import config
    import dataset
    import model as model_module

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def plot_combined_history(
    history_phase1: tf.keras.callbacks.History,
    history_phase2: tf.keras.callbacks.History,
    output_path: Path = config.TRAINING_HISTORY_PLOT_PATH
) -> None:
    """
    Plots training and validation loss and accuracy across both Phase 1 and Phase 2.
    """
    acc = history_phase1.history.get("accuracy", []) + history_phase2.history.get("accuracy", [])
    val_acc = history_phase1.history.get("val_accuracy", []) + history_phase2.history.get("val_accuracy", [])
    loss = history_phase1.history.get("loss", []) + history_phase2.history.get("loss", [])
    val_loss = history_phase1.history.get("val_loss", []) + history_phase2.history.get("val_loss", [])

    epochs_range = range(1, len(acc) + 1)
    phase1_len = len(history_phase1.history.get("accuracy", []))

    plt.figure(figsize=(14, 5))

    # Accuracy Plot
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label="Training Accuracy", color="#2563EB", linewidth=2)
    plt.plot(epochs_range, val_acc, label="Validation Accuracy", color="#10B981", linewidth=2)
    if phase1_len > 0 and phase1_len < len(acc):
        plt.axvline(x=phase1_len, color="#F59E0B", linestyle="--", label="Fine-Tuning Start")
    plt.title("SKYsense AI - Accuracy Curve (Two-Phase)")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.ylim([0.0, 1.05])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right")

    # Loss Plot
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label="Training Loss", color="#EF4444", linewidth=2)
    plt.plot(epochs_range, val_loss, label="Validation Loss", color="#8B5CF6", linewidth=2)
    if phase1_len > 0 and phase1_len < len(loss):
        plt.axvline(x=phase1_len, color="#F59E0B", linestyle="--", label="Fine-Tuning Start")
    plt.title("SKYsense AI - Loss Curve (Two-Phase)")
    plt.xlabel("Epoch")
    plt.ylabel("Categorical Crossentropy Loss")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Training history visualization saved to: {output_path}")


def run_training(
    phase1_epochs: int = config.PHASE1_EPOCHS,
    phase2_epochs: int = config.PHASE2_EPOCHS,
    batch_size: int = config.BATCH_SIZE
) -> Dict[str, Any]:
    """
    Executes the end-to-end two-phase training pipeline.
    """
    logger.info("Initializing Data Generators...")
    train_gen, val_gen, test_gen = dataset.get_data_generators(batch_size=batch_size)

    logger.info("Building Model Architecture...")
    model, base_model = model_module.build_model()

    # Callbacks Configuration
    csv_logger = CSVLogger(str(config.LOGS_DIR / "training_log.csv"), append=False)
    checkpoint_callback = ModelCheckpoint(
        filepath=str(config.BEST_MODEL_PATH),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1
    )
    early_stop_p1 = EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True,
        verbose=1
    )
    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )

    # ==========================================
    # PHASE 1: Frozen Backbone Feature Extraction
    # ==========================================
    logger.info(f"--- Starting Phase 1 Training ({phase1_epochs} Epochs, LR={config.PHASE1_INITIAL_LR}) ---")
    model_module.freeze_backbone(base_model)
    model_module.compile_model(model, learning_rate=config.PHASE1_INITIAL_LR)

    history_phase1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=phase1_epochs,
        callbacks=[checkpoint_callback, early_stop_p1, csv_logger]
    )

    # ==========================================
    # PHASE 2: Fine-Tuning Full Backbone
    # ==========================================
    logger.info(f"--- Starting Phase 2 Fine-Tuning ({phase2_epochs} Epochs, LR={config.PHASE2_FINE_TUNE_LR}) ---")
    model_module.unfreeze_backbone(base_model)
    model_module.compile_model(model, learning_rate=config.PHASE2_FINE_TUNE_LR)

    early_stop_p2 = EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True,
        verbose=1
    )

    history_phase2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=phase2_epochs,
        callbacks=[checkpoint_callback, early_stop_p2, reduce_lr, csv_logger]
    )

    # Save Final Model
    config.FINAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(config.FINAL_MODEL_PATH))
    logger.info(f"Final model weights saved to: {config.FINAL_MODEL_PATH}")

    # Export TFLite Model
    try:
        model_module.export_to_tflite(model, config.TFLITE_MODEL_PATH)
    except Exception as e:
        logger.error(f"TFLite export error: {e}")

    # Plot & Save Combined History
    plot_combined_history(history_phase1, history_phase2)

    # Record Training Summary Metrics
    training_summary = {
        "phase1": {
            "epochs_run": len(history_phase1.history.get("accuracy", [])),
            "final_train_acc": float(history_phase1.history.get("accuracy", [0])[-1]),
            "final_val_acc": float(history_phase1.history.get("val_accuracy", [0])[-1]),
            "best_val_acc": float(max(history_phase1.history.get("val_accuracy", [0]))),
        },
        "phase2": {
            "epochs_run": len(history_phase2.history.get("accuracy", [])),
            "final_train_acc": float(history_phase2.history.get("accuracy", [0])[-1]),
            "final_val_acc": float(history_phase2.history.get("val_accuracy", [0])[-1]),
            "best_val_acc": float(max(history_phase2.history.get("val_accuracy", [0]))),
        },
        "artifacts": {
            "best_model": str(config.BEST_MODEL_PATH),
            "final_model": str(config.FINAL_MODEL_PATH),
            "tflite_model": str(config.TFLITE_MODEL_PATH),
            "history_plot": str(config.TRAINING_HISTORY_PLOT_PATH),
        }
    }

    with open(config.TRAINING_METRICS_PATH, "w") as f:
        json.dump(training_summary, f, indent=2)

    logger.info(f"Training metadata recorded to: {config.TRAINING_METRICS_PATH}")
    return training_summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SKYsense AI - Train Baseline Model")
    parser.add_argument("--phase1-epochs", type=int, default=config.PHASE1_EPOCHS, help="Epochs for Phase 1 (frozen backbone)")
    parser.add_argument("--phase2-epochs", type=int, default=config.PHASE2_EPOCHS, help="Epochs for Phase 2 (fine-tuning)")
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE, help="Batch size")
    args = parser.parse_args()

    run_training(
        phase1_epochs=args.phase1_epochs,
        phase2_epochs=args.phase2_epochs,
        batch_size=args.batch_size
    )

