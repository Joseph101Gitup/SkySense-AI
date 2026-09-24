"""
SKYsense AI - Dataset Preparation, Stratified Splitting & Generator Module
Handles downloading, meteorological mapping, verified stratified splitting (70/15/15),
and disjoint generation for Train, Validation, and Test partitions.
Pure Python & NumPy implementation ensures compatibility across restricted OS policies.
"""

import os
import shutil
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator

try:
    from . import config
except ImportError:
    import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def locate_or_download_ccsn(download_dir: Path = config.RAW_DATA_DIR) -> Path:
    """
    Locates the CCSN dataset directory containing the 11 cloud folders.
    If not already downloaded locally, uses kagglehub to fetch the public dataset.
    """
    required_cloud_folders = ["Ci", "Cs", "Cc", "Ac", "As", "Sc", "St", "Ns", "Cb", "Cu", "Ct"]
    
    # 1. Search inside local raw data dir
    if download_dir.exists():
        for root, dirs, _ in os.walk(download_dir):
            if all(folder in dirs for folder in required_cloud_folders):
                logger.info(f"CCSN dataset cloud folders located locally at: {root}")
                return Path(root)

    # 2. Check KaggleHub cache directory directly
    user_home = Path.home()
    kagglehub_cache = user_home / ".cache" / "kagglehub" / "datasets" / "mmichelli" / "cirrus-cumulus-stratus-nimbus-ccsn-database"
    if kagglehub_cache.exists():
        for root, dirs, _ in os.walk(kagglehub_cache):
            if all(folder in dirs for folder in required_cloud_folders):
                logger.info(f"Found CCSN dataset in existing KaggleHub cache: {root}")
                return Path(root)

    # 3. Download via KaggleHub
    logger.info("CCSN dataset not found locally. Initiating download via KaggleHub...")
    import kagglehub
    download_path = kagglehub.dataset_download(config.KAGGLE_DATASET_ID)
    logger.info(f"KaggleHub downloaded files to: {download_path}")

    for root, dirs, _ in os.walk(download_path):
        if all(folder in dirs for folder in required_cloud_folders):
            logger.info(f"Found source cloud directories at: {root}")
            return Path(root)

    for root, dirs, _ in os.walk(download_path):
        if any(c in dirs for c in ["Ci", "Cb", "As", "Cu"]):
            logger.info(f"Found candidate cloud directory at: {root}")
            return Path(root)

    raise FileNotFoundError(f"Could not locate cloud folders in {download_path}")


def prepare_processed_dataset(source_dir: Path, output_dir: Path = config.PROCESSED_DATA_DIR) -> Dict[str, int]:
    """
    Sorts and aggregates the 11 cloud directories into the 3 verified rainfall categories.
    Verifies that the total image count equals exactly 2,543 images.
    """
    logger.info(f"Aggregating 11 cloud classes into 3 rainfall categories at: {output_dir}")

    for class_name in config.CLASS_NAMES:
        (output_dir / class_name).mkdir(parents=True, exist_ok=True)

    counts = {c: 0 for c in config.CLASS_NAMES}
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    for rain_class, cloud_folders in config.CLOUD_TO_RAIN_MAPPING.items():
        target_class_dir = output_dir / rain_class
        for cloud_folder in cloud_folders:
            folder_path = source_dir / cloud_folder
            if not folder_path.exists():
                logger.warning(f"Cloud folder '{cloud_folder}' does not exist at {folder_path}")
                continue

            for file in folder_path.iterdir():
                if file.is_file() and file.suffix.lower() in image_extensions:
                    dest_file = target_class_dir / f"{cloud_folder}_{file.name}"
                    if not dest_file.exists():
                        shutil.copy2(file, dest_file)
                    counts[rain_class] += 1

    total_images = sum(counts.values())
    logger.info(f"Dataset aggregation completed. Total images: {total_images}")
    for c, cnt in counts.items():
        expected = config.EXPECTED_CLASS_COUNTS[c]
        logger.info(f"  Class '{c}': {cnt} images (Expected: {expected})")
        if cnt != expected:
            logger.warning(f"Count mismatch for '{c}': Found {cnt}, expected {expected}")

    return counts


def create_stratified_splits(
    processed_dir: Path = config.PROCESSED_DATA_DIR,
    splits_dir: Path = config.SPLITS_DIR,
    train_ratio: float = config.TRAIN_RATIO,
    val_ratio: float = config.VAL_RATIO,
    test_ratio: float = config.TEST_RATIO,
    seed: int = config.RANDOM_SEED
) -> Dict[str, Dict[str, int]]:
    """
    Performs deterministic stratified splitting (70% train / 15% validation / 15% test).
    Verifies that partitions are completely disjoint:
      Train ∩ Validation = 0
      Train ∩ Test = 0
      Validation ∩ Test = 0
    """
    logger.info(f"Creating stratified splits ({train_ratio*100:.0f}% / {val_ratio*100:.0f}% / {test_ratio*100:.0f}%) with seed {seed}...")

    # Clean existing splits to guarantee fresh generation
    for split_name in ["train", "val", "test"]:
        split_path = splits_dir / split_name
        if split_path.exists():
            shutil.rmtree(split_path)
        for class_name in config.CLASS_NAMES:
            (split_path / class_name).mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    train_manifest = []
    val_manifest = []
    test_manifest = []

    class_counts = {"train": {}, "val": {}, "test": {}, "total": {}}

    for class_name in config.CLASS_NAMES:
        class_folder = processed_dir / class_name
        files = sorted([f for f in class_folder.iterdir() if f.is_file()])
        total_cls_samples = len(files)
        class_counts["total"][class_name] = total_cls_samples

        # Deterministic shuffle per class
        shuffled = files.copy()
        rng.shuffle(shuffled)

        n_train = int(round(total_cls_samples * train_ratio))
        n_val = int(round(total_cls_samples * val_ratio))
        # Remaining goes to test to guarantee conservation of all samples
        n_test = total_cls_samples - n_train - n_val

        train_slice = shuffled[:n_train]
        val_slice = shuffled[n_train:n_train + n_val]
        test_slice = shuffled[n_train + n_val:]

        assert len(train_slice) + len(val_slice) + len(test_slice) == total_cls_samples

        class_counts["train"][class_name] = len(train_slice)
        class_counts["val"][class_name] = len(val_slice)
        class_counts["test"][class_name] = len(test_slice)

        def copy_files(file_list, split_name):
            manifest = []
            for file_path in file_list:
                dest = splits_dir / split_name / class_name / file_path.name
                shutil.copy2(file_path, dest)
                manifest.append(f"{class_name}/{file_path.name}")
            return manifest

        train_manifest.extend(copy_files(train_slice, "train"))
        val_manifest.extend(copy_files(val_slice, "val"))
        test_manifest.extend(copy_files(test_slice, "test"))

    # STRICT DISJOINT ASSERTIONS
    set_train = set(train_manifest)
    set_val = set(val_manifest)
    set_test = set(test_manifest)

    train_val_overlap = set_train.intersection(set_val)
    train_test_overlap = set_train.intersection(set_test)
    val_test_overlap = set_val.intersection(set_test)

    assert len(train_val_overlap) == 0, f"Critical Leak: Train & Val overlap: {train_val_overlap}"
    assert len(train_test_overlap) == 0, f"Critical Leak: Train & Test overlap: {train_test_overlap}"
    assert len(val_test_overlap) == 0, f"Critical Leak: Val & Test overlap: {val_test_overlap}"
    total_split_count = len(set_train) + len(set_val) + len(set_test)
    assert total_split_count == config.TOTAL_VERIFIED_IMAGES, (
        f"Total count mismatch: {total_split_count} vs {config.TOTAL_VERIFIED_IMAGES}"
    )

    logger.info("Disjoint partition verification PASSED: (Train ∩ Val = 0, Train ∩ Test = 0, Val ∩ Test = 0)")

    distribution_report = {
        "train": class_counts["train"],
        "val": class_counts["val"],
        "test": class_counts["test"],
        "total": class_counts["total"],
        "summary": {
            "train_count": len(train_manifest),
            "val_count": len(val_manifest),
            "test_count": len(test_manifest),
            "total_count": total_split_count,
            "random_seed": seed,
            "train_percentage": round(len(train_manifest) / total_split_count * 100, 2),
            "val_percentage": round(len(val_manifest) / total_split_count * 100, 2),
            "test_percentage": round(len(test_manifest) / total_split_count * 100, 2),
        }
    }

    # Save manifest and reports
    manifest_data = {
        "random_seed": seed,
        "train_files": train_manifest,
        "val_files": val_manifest,
        "test_files": test_manifest,
    }
    with open(config.SPLIT_MANIFEST_PATH, "w") as f:
        json.dump(manifest_data, f, indent=2)

    with open(config.CLASS_DISTRIBUTION_PATH, "w") as f:
        json.dump(distribution_report, f, indent=2)

    logger.info(f"Split distribution saved to: {config.CLASS_DISTRIBUTION_PATH}")
    logger.info(f"Train samples: {len(train_manifest)} ({distribution_report['summary']['train_percentage']}%)")
    logger.info(f"Val samples:   {len(val_manifest)} ({distribution_report['summary']['val_percentage']}%)")
    logger.info(f"Test samples:  {len(test_manifest)} ({distribution_report['summary']['test_percentage']}%)")

    return distribution_report


def get_data_generators(
    splits_dir: Path = config.SPLITS_DIR,
    target_size: Tuple[int, int] = config.IMAGE_SIZE,
    batch_size: int = config.BATCH_SIZE
) -> Tuple[ImageDataGenerator, ImageDataGenerator, ImageDataGenerator]:
    """
    Constructs data generators with strict methodological integrity:
      - Training: Pixel rescaling (1/255) + Data Augmentation (Rotation, Shifts, Horizontal Flip)
      - Validation: Pixel rescaling (1/255) ONLY (No Augmentation)
      - Test: Pixel rescaling (1/255) ONLY (No Augmentation, shuffle=False)
    """
    train_dir = splits_dir / "train"
    val_dir = splits_dir / "val"
    test_dir = splits_dir / "test"

    # 1. Training Generator with Data Augmentation
    train_datagen = ImageDataGenerator(
        rescale=config.PIXEL_RESCALE,
        rotation_range=config.AUGMENTATION_CONFIG["rotation_range"],
        width_shift_range=config.AUGMENTATION_CONFIG["width_shift_range"],
        height_shift_range=config.AUGMENTATION_CONFIG["height_shift_range"],
        horizontal_flip=config.AUGMENTATION_CONFIG["horizontal_flip"],
        fill_mode=config.AUGMENTATION_CONFIG["fill_mode"]
    )

    train_generator = train_datagen.flow_from_directory(
        directory=str(train_dir),
        target_size=target_size,
        batch_size=batch_size,
        class_mode="categorical",
        classes=config.CLASS_NAMES,
        shuffle=True,
        seed=config.RANDOM_SEED
    )

    # 2. Validation Generator with Rescaling ONLY
    val_datagen = ImageDataGenerator(rescale=config.PIXEL_RESCALE)

    val_generator = val_datagen.flow_from_directory(
        directory=str(val_dir),
        target_size=target_size,
        batch_size=batch_size,
        class_mode="categorical",
        classes=config.CLASS_NAMES,
        shuffle=False
    )

    # 3. Test Generator with Rescaling ONLY
    test_datagen = ImageDataGenerator(rescale=config.PIXEL_RESCALE)

    test_generator = test_datagen.flow_from_directory(
        directory=str(test_dir),
        target_size=target_size,
        batch_size=batch_size,
        class_mode="categorical",
        classes=config.CLASS_NAMES,
        shuffle=False
    )

    # STRICT CLASS INDEX VERIFICATION
    assert train_generator.class_indices == config.CLASS_TO_IDX, (
        f"Train generator class mapping mismatch: {train_generator.class_indices} vs {config.CLASS_TO_IDX}"
    )
    assert val_generator.class_indices == config.CLASS_TO_IDX, (
        f"Validation generator class mapping mismatch: {val_generator.class_indices} vs {config.CLASS_TO_IDX}"
    )
    assert test_generator.class_indices == config.CLASS_TO_IDX, (
        f"Test generator class mapping mismatch: {test_generator.class_indices} vs {config.CLASS_TO_IDX}"
    )

    logger.info(f"Verified generator class mapping: {train_generator.class_indices}")

    return train_generator, val_generator, test_generator


if __name__ == "__main__":
    logger.info("Executing dataset preparation and splitting verification pipeline...")
    src_dir = locate_or_download_ccsn()
    counts = prepare_processed_dataset(src_dir)
    splits = create_stratified_splits()
    train_gen, val_gen, test_gen = get_data_generators()
    logger.info("Dataset preparation pipeline completed successfully.")
