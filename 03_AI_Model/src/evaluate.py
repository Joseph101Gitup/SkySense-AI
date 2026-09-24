"""
SKYsense AI - Comprehensive Test Set Evaluation Module
Evaluates model on the strictly held-out, unaugmented test partition,
computing Confusion Matrix, Classification Report, Precision, Recall, F1-Score,
Test Loss, and Test Accuracy using pure NumPy for high portability.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf

try:
    from . import config
    from . import dataset
except ImportError:
    import config
    import dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_probs: np.ndarray, class_names: List[str]) -> Dict[str, Any]:
    """
    Computes confusion matrix, per-class precision, recall, F1, and summary averages.
    Implemented in pure NumPy for deterministic, cross-platform execution.
    """
    num_classes = len(class_names)
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1

    total_samples = len(y_true)
    overall_acc = float(np.mean(y_true == y_pred))

    # Categorical Crossentropy Loss
    eps = 1e-15
    clipped = np.clip(y_probs, eps, 1.0 - eps)
    y_true_onehot = np.eye(num_classes)[y_true]
    test_loss = float(-np.mean(np.sum(y_true_onehot * np.log(clipped), axis=1)))

    report_dict = {}
    class_precisions = []
    class_recalls = []
    class_f1s = []
    supports = []

    for i, name in enumerate(class_names):
        tp = int(cm[i, i])
        fp = int(np.sum(cm[:, i]) - tp)
        fn = int(np.sum(cm[i, :]) - tp)
        support = int(np.sum(cm[i, :]))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        report_dict[name] = {
            "precision": prec,
            "recall": rec,
            "f1-score": f1,
            "support": support
        }
        class_precisions.append(prec)
        class_recalls.append(rec)
        class_f1s.append(f1)
        supports.append(support)

    # Macro Averages
    macro_prec = float(np.mean(class_precisions))
    macro_rec = float(np.mean(class_recalls))
    macro_f1 = float(np.mean(class_f1s))

    # Weighted Averages
    weights = np.array(supports) / total_samples
    weighted_prec = float(np.sum(np.array(class_precisions) * weights))
    weighted_rec = float(np.sum(np.array(class_recalls) * weights))
    weighted_f1 = float(np.sum(np.array(class_f1s) * weights))

    report_dict["accuracy"] = overall_acc
    report_dict["macro avg"] = {
        "precision": macro_prec,
        "recall": macro_rec,
        "f1-score": macro_f1,
        "support": total_samples
    }
    report_dict["weighted avg"] = {
        "precision": weighted_prec,
        "recall": weighted_rec,
        "f1-score": weighted_f1,
        "support": total_samples
    }

    # Format text table
    header = f"{'':>24} {'precision':>10} {'recall':>10} {'f1-score':>10} {'support':>10}\n\n"
    lines = [header]
    for name in class_names:
        s = report_dict[name]
        lines.append(f"{name:>24} {s['precision']:>10.4f} {s['recall']:>10.4f} {s['f1-score']:>10.4f} {s['support']:>10d}\n")
    lines.append("\n")
    lines.append(f"{'accuracy':>24} {'':>10} {'':>10} {overall_acc:>10.4f} {total_samples:>10d}\n")
    m = report_dict["macro avg"]
    lines.append(f"{'macro avg':>24} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1-score']:>10.4f} {m['support']:>10d}\n")
    w = report_dict["weighted avg"]
    lines.append(f"{'weighted avg':>24} {w['precision']:>10.4f} {w['recall']:>10.4f} {w['f1-score']:>10.4f} {w['support']:>10d}\n")
    report_text = "".join(lines)

    return {
        "confusion_matrix": cm,
        "test_accuracy": overall_acc,
        "test_loss": test_loss,
        "report_dict": report_dict,
        "report_text": report_text
    }


def evaluate_model(
    model_path: Path = config.BEST_MODEL_PATH,
    test_gen: tf.keras.preprocessing.image.DirectoryIterator = None,
    save_plots: bool = True
) -> Dict[str, Any]:
    """
    Executes comprehensive evaluation of the specified model weights on the independent test set.
    """
    logger.info(f"Loading evaluation model weights from: {model_path}")
    if not model_path.exists():
        fallback_path = config.FINAL_MODEL_PATH
        if fallback_path.exists():
            logger.warning(f"Best model not found at {model_path}. Falling back to final model: {fallback_path}")
            model_path = fallback_path
        else:
            raise FileNotFoundError(f"Model file not found at {model_path} or {fallback_path}")

    model = tf.keras.models.load_model(str(model_path))

    if test_gen is None:
        _, _, test_gen = dataset.get_data_generators()

    test_gen.reset()
    num_test_samples = len(test_gen.filenames)
    logger.info(f"Evaluating {num_test_samples} independent test images...")

    # Predict probabilities on test set
    y_pred_probs = model.predict(test_gen, verbose=1)
    y_pred_indices = np.argmax(y_pred_probs, axis=1)
    y_true_indices = np.array(test_gen.classes)

    assert test_gen.class_indices == config.CLASS_TO_IDX, (
        f"Mismatch: generator class_indices {test_gen.class_indices} vs config {config.CLASS_TO_IDX}"
    )

    metrics = compute_classification_metrics(
        y_true_indices,
        y_pred_indices,
        y_pred_probs,
        config.CLASS_NAMES
    )

    cm = metrics["confusion_matrix"]
    cm_norm = cm.astype("float") / np.maximum(cm.sum(axis=1)[:, np.newaxis], 1)
    report_dict = metrics["report_dict"]
    report_text = metrics["report_text"]

    if save_plots:
        _plot_confusion_matrices(cm, cm_norm)

    config.EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.CLASSIFICATION_REPORT_PATH, "w") as f:
        json.dump(report_dict, f, indent=2)

    with open(config.EVALUATION_DIR / "classification_report.txt", "w") as f:
        f.write(report_text)

    summary = {
        "model_path": str(model_path),
        "total_test_samples": num_test_samples,
        "test_accuracy": round(metrics["test_accuracy"], 4),
        "test_loss": round(metrics["test_loss"], 4),
        "macro_avg_f1": round(report_dict["macro avg"]["f1-score"], 4),
        "weighted_avg_f1": round(report_dict["weighted avg"]["f1-score"], 4),
        "class_breakdown": {
            cls_name: {
                "precision": round(report_dict[cls_name]["precision"], 4),
                "recall": round(report_dict[cls_name]["recall"], 4),
                "f1_score": round(report_dict[cls_name]["f1-score"], 4),
                "support": int(report_dict[cls_name]["support"])
            }
            for cls_name in config.CLASS_NAMES
        },
        "confusion_matrix": cm.tolist()
    }

    with open(config.TEST_METRICS_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    _print_evaluation_summary(summary, report_text)
    return summary


def _plot_confusion_matrices(cm: np.ndarray, cm_norm: np.ndarray) -> None:
    """Generates and saves raw and normalized confusion matrix plots."""
    # 1. Raw Counts
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=config.CLASS_NAMES,
        yticklabels=config.CLASS_NAMES,
        cbar=False
    )
    plt.title("SKYsense AI - Test Confusion Matrix (Counts)", fontsize=13, fontweight="bold")
    plt.xlabel("Predicted Rainfall Class", fontsize=11)
    plt.ylabel("True Rainfall Class", fontsize=11)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(config.CONFUSION_MATRIX_PLOT_PATH, dpi=300)
    plt.close()

    # 2. Normalized Percentage
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm_norm * 100.0,
        annot=True,
        fmt=".1f",
        cmap="Greens",
        xticklabels=config.CLASS_NAMES,
        yticklabels=config.CLASS_NAMES,
        cbar=False
    )
    plt.title("SKYsense AI - Normalized Test Confusion Matrix (%)", fontsize=13, fontweight="bold")
    plt.xlabel("Predicted Rainfall Class", fontsize=11)
    plt.ylabel("True Rainfall Class", fontsize=11)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(config.CONFUSION_MATRIX_NORMALIZED_PATH, dpi=300)
    plt.close()
    logger.info("Confusion matrix plots successfully saved.")


def _print_evaluation_summary(summary: Dict[str, Any], report_text: str) -> None:
    """Prints a clean terminal evaluation banner."""
    print("\n" + "=" * 65)
    print("           SKYSENSE AI - INDEPENDENT TEST SET EVALUATION")
    print("=" * 65)
    print(f" Test Accuracy  : {summary['test_accuracy'] * 100:.2f}%")
    print(f" Test Loss      : {summary['test_loss']:.4f}")
    print(f" Macro Avg F1   : {summary['macro_avg_f1'] * 100:.2f}%")
    print(f" Weighted Avg F1: {summary['weighted_avg_f1'] * 100:.2f}%")
    print("-" * 65)
    print(" Classification Report:")
    print(report_text)
    print("=" * 65 + "\n")


if __name__ == "__main__":
    evaluate_model()
