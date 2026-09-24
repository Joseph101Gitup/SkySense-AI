"""
SKYsense AI - Central Configuration Module
Defines all directory paths, hyperparameter specifications, dataset constants,
and verified class mappings.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AI_DIR = PROJECT_ROOT / "03_AI_Model"

# Dataset Directories
DATASETS_DIR = AI_DIR / "datasets"
RAW_DATA_DIR = DATASETS_DIR / "raw"
PROCESSED_DATA_DIR = DATASETS_DIR / "processed"
SPLITS_DIR = DATASETS_DIR / "splits"
TRAIN_DIR = SPLITS_DIR / "train"
VAL_DIR = SPLITS_DIR / "val"
TEST_DIR = SPLITS_DIR / "test"

# Output & Artifact Directories
MODELS_DIR = AI_DIR / "models"
EVALUATION_DIR = AI_DIR / "evaluation"
RESULTS_DIR = AI_DIR / "results"
LOGS_DIR = AI_DIR / "logs"

# Ensure all directories exist
for directory in [DATASETS_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SPLITS_DIR,
                  TRAIN_DIR, VAL_DIR, TEST_DIR, MODELS_DIR, EVALUATION_DIR,
                  RESULTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Dataset Identification & Verification
KAGGLE_DATASET_ID = "mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database"
TOTAL_VERIFIED_IMAGES = 2543

# Verified Class Names & Alphabetical Index Mapping
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

IDX_TO_CLASS = {v: k for k, v in CLASS_TO_IDX.items()}

# Verified Counts per Category
EXPECTED_CLASS_COUNTS = {
    "Low_to_Medium_Rain": 1004,
    "Medium_to_Heavy_Rain": 624,
    "No_to_Low_Rain": 915,
}

# Scientific Meteorological Mapping from CCSN Cloud Types
CLOUD_TO_RAIN_MAPPING = {
    "Low_to_Medium_Rain": ["As", "Sc", "St", "Ns"],
    "Medium_to_Heavy_Rain": ["Cb", "Cu", "Ct"],
    "No_to_Low_Rain": ["Ci", "Cs", "Cc", "Ac"],
}

# Dataset Splitting Parameters
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
RANDOM_SEED = 42

# Image Preprocessing & Input Specifications
IMAGE_HEIGHT = 256
IMAGE_WIDTH = 256
IMAGE_SIZE = (IMAGE_HEIGHT, IMAGE_WIDTH)
IMAGE_CHANNELS = 3
INPUT_SHAPE = (IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_CHANNELS)
BATCH_SIZE = 32
PIXEL_RESCALE = 1.0 / 255.0

# Augmentation Parameters (Training Only)
AUGMENTATION_CONFIG = {
    "rotation_range": 25,
    "width_shift_range": 0.2,
    "height_shift_range": 0.2,
    "horizontal_flip": True,
    "fill_mode": "nearest",
}

# Model Architecture & Hyperparameters
BACKBONE_NAME = "Xception"
DROPOUT_RATE = 0.4
NUM_CLASSES = len(CLASS_NAMES)

# Two-Phase Training Schedule
PHASE1_EPOCHS = 15
PHASE1_INITIAL_LR = 1e-3

PHASE2_EPOCHS = 15
PHASE2_FINE_TUNE_LR = 1e-5

# Artifact File Paths
BEST_MODEL_PATH = MODELS_DIR / "best_xception_rainfall.keras"
FINAL_MODEL_PATH = MODELS_DIR / "final_xception_rainfall.keras"
TFLITE_MODEL_PATH = MODELS_DIR / "xception_rainfall.tflite"
SPLIT_MANIFEST_PATH = RESULTS_DIR / "dataset_split_manifest.json"
CLASS_DISTRIBUTION_PATH = RESULTS_DIR / "class_distribution_report.json"
TRAINING_HISTORY_PLOT_PATH = RESULTS_DIR / "training_history.png"
TRAINING_METRICS_PATH = RESULTS_DIR / "training_metrics.json"
CONFUSION_MATRIX_PLOT_PATH = EVALUATION_DIR / "confusion_matrix.png"
CONFUSION_MATRIX_NORMALIZED_PATH = EVALUATION_DIR / "confusion_matrix_normalized.png"
CLASSIFICATION_REPORT_PATH = EVALUATION_DIR / "classification_report.json"
TEST_METRICS_PATH = EVALUATION_DIR / "test_evaluation_summary.json"
