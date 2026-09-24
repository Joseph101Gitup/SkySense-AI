"""
SKYsense AI - Model Architecture Definition & Transfer Learning Management
Implements Xception transfer learning backbone with custom classification head,
frozen/unfrozen phase management, and TFLite production export.
"""

import io
import logging
from pathlib import Path
from typing import Tuple
import tensorflow as tf
from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

try:
    from . import config
except ImportError:
    import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_model(
    input_shape: Tuple[int, int, int] = config.INPUT_SHAPE,
    num_classes: int = config.NUM_CLASSES,
    dropout_rate: float = config.DROPOUT_RATE
) -> Tuple[Model, Model]:
    """
    Constructs the Xception-based transfer learning model for rainfall classification.
    Returns:
        model: The complete end-to-end Keras Model.
        base_model: The underlying Xception feature extraction backbone.
    """
    logger.info(f"Building Xception baseline (Input: {input_shape}, Classes: {num_classes}, Dropout: {dropout_rate})...")

    # Load pre-trained Xception with ImageNet weights, omitting original classifier
    base_model = Xception(
        weights="imagenet",
        include_top=False,
        input_shape=input_shape
    )

    # Freeze base model by default for Phase 1 feature extraction
    base_model.trainable = False

    # Define custom top classification layers
    inputs = base_model.input
    x = base_model.output
    x = GlobalAveragePooling2D(name="global_average_pooling2d")(x)
    x = Dropout(dropout_rate, name="dropout_regularization")(x)
    outputs = Dense(num_classes, activation="softmax", name="rainfall_predictions")(x)

    model = Model(inputs=inputs, outputs=outputs, name="SkySense_Xception_Baseline")
    logger.info("Xception baseline architecture constructed successfully.")
    return model, base_model


def freeze_backbone(base_model: Model) -> None:
    """Freezes all layers in the base Xception backbone for Phase 1 feature extraction."""
    base_model.trainable = False
    logger.info("Base Xception backbone frozen. Only top classification layers are trainable.")


def unfreeze_backbone(base_model: Model) -> None:
    """Unfreezes all layers in the base Xception backbone for Phase 2 fine-tuning."""
    base_model.trainable = True
    logger.info("Base Xception backbone unfrozen. Full network is trainable.")


def compile_model(
    model: Model,
    learning_rate: float,
    loss: str = "categorical_crossentropy",
    metrics: list = None
) -> None:
    """Compiles the model with specified learning rate and loss."""
    if metrics is None:
        metrics = ["accuracy"]
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    logger.info(f"Model compiled with Adam(lr={learning_rate:.1e}), loss='{loss}', metrics={metrics}")


def get_model_summary_str(model: Model) -> str:
    """Returns the model summary as a formatted string."""
    stream = io.StringIO()
    model.summary(print_fn=lambda x: stream.write(x + "\n"))
    return stream.getvalue()


def export_to_tflite(model: Model, output_path: Path = config.TFLITE_MODEL_PATH) -> Path:
    """
    Converts and exports the trained Keras model to TensorFlow Lite (TFLite)
    for lightweight edge, mobile, and production deployment.
    """
    logger.info(f"Exporting model to TensorFlow Lite format: {output_path}")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # Enable standard optimization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"TFLite model successfully exported ({file_size_mb:.2f} MB).")
    return output_path


if __name__ == "__main__":
    m, b = build_model()
    compile_model(m, learning_rate=config.PHASE1_INITIAL_LR)
    print(get_model_summary_str(m))
