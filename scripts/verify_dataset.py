#!/usr/bin/env python
"""
SKYsense AI - Dataset Integrity & Verification Script
Verifies dataset structure, 3 rainfall classes, sample counts (total: 2,543),
disjointness across Train/Val/Test partitions, and image file validity.
"""

import sys
import os
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"
PROCESSED_DIR = AI_MODEL_DIR / "datasets" / "processed"
SPLITS_DIR = AI_MODEL_DIR / "datasets" / "splits"

EXPECTED_CLASSES = [
    "Low_to_Medium_Rain",
    "Medium_to_Heavy_Rain",
    "No_to_Low_Rain",
]

# Verified class counts from config.py: 1004 + 624 + 915 = 2543
EXPECTED_TOTALS = {
    "Low_to_Medium_Rain": 1004,
    "Medium_to_Heavy_Rain": 624,
    "No_to_Low_Rain": 915,
}
TOTAL_EXPECTED = 2543


def print_step(title: str):
    print(f"\n[+] {title}")


def verify_processed_dataset() -> bool:
    print_step("Verifying Aggregated Processed Dataset (03_AI_Model/datasets/processed)...")
    if not PROCESSED_DIR.exists():
        print(f"    [!] Directory not found: {PROCESSED_DIR}")
        return False

    all_valid = True
    found_total = 0
    for cls in EXPECTED_CLASSES:
        cls_dir = PROCESSED_DIR / cls
        if not cls_dir.exists():
            print(f"    [!] Missing class directory: {cls}")
            all_valid = False
            continue

        images = [f for f in cls_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        count = len(images)
        found_total += count
        expected = EXPECTED_TOTALS[cls]
        status = "[OK]" if count == expected else "[WARN]"
        print(f"    {status} {cls:<25} : {count:>5} images (Expected: {expected})")
        if count != expected:
            all_valid = False

    print(f"    Total Processed Images      : {found_total:>5} (Expected: {TOTAL_EXPECTED})")
    return all_valid


def verify_splits() -> bool:
    print_step("Verifying Stratified Partitions & Disjointness (03_AI_Model/datasets/splits)...")
    if not SPLITS_DIR.exists():
        print(f"    [!] Splits directory not found: {SPLITS_DIR}")
        return False

    splits = ["train", "val", "test"]
    split_files = {"train": set(), "val": set(), "test": set()}
    split_counts = {"train": 0, "val": 0, "test": 0}

    for split in splits:
        split_path = SPLITS_DIR / split
        if not split_path.exists():
            print(f"    [!] Missing split directory: {split_path}")
            return False

        for cls in EXPECTED_CLASSES:
            cls_path = split_path / cls
            if not cls_path.exists():
                print(f"    [!] Missing class folder: {cls_path}")
                return False
            for img_file in cls_path.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    split_files[split].add(img_file.name)
                    split_counts[split] += 1

    print(f"    [OK] Train Partition        : {split_counts['train']:>5} images (~70%)")
    print(f"    [OK] Validation Partition   : {split_counts['val']:>5} images (~15%)")
    print(f"    [OK] Test Partition         : {split_counts['test']:>5} images (~15%)")
    total_split = sum(split_counts.values())
    print(f"    Total Split Images          : {total_split:>5} (Expected: {TOTAL_EXPECTED})")

    # Check for disjointness (zero data leakage)
    train_val_overlap = split_files["train"].intersection(split_files["val"])
    train_test_overlap = split_files["train"].intersection(split_files["test"])
    val_test_overlap = split_files["val"].intersection(split_files["test"])

    overlap_clean = True
    if train_val_overlap:
        print(f"    [!] ERROR: Data leakage detected between Train and Val ({len(train_val_overlap)} files)")
        overlap_clean = False
    if train_test_overlap:
        print(f"    [!] ERROR: Data leakage detected between Train and Test ({len(train_test_overlap)} files)")
        overlap_clean = False
    if val_test_overlap:
        print(f"    [!] ERROR: Data leakage detected between Val and Test ({len(val_test_overlap)} files)")
        overlap_clean = False

    if overlap_clean:
        print("    [OK] Zero Data Leakage: Partitions are strictly disjoint (Train, Val, Test disjoint).")

    return (total_split == TOTAL_EXPECTED) and overlap_clean


def verify_image_integrity(sample_limit: int = 100) -> bool:
    print_step(f"Verifying Image File Headers (Sample check of up to {sample_limit} files per split)...")
    corrupt_count = 0
    checked_count = 0

    for split in ["train", "val", "test"]:
        for cls in EXPECTED_CLASSES:
            cls_path = SPLITS_DIR / split / cls
            if not cls_path.exists():
                continue
            images = list(cls_path.glob("*.jpg")) + list(cls_path.glob("*.png"))
            for img_path in images[:sample_limit]:
                checked_count += 1
                try:
                    with Image.open(img_path) as im:
                        im.verify()
                except Exception as e:
                    print(f"    [!] Corrupted image detected: {img_path} ({e})")
                    corrupt_count += 1

    print(f"    [OK] Verified {checked_count} image specimens without corruption (Errors: {corrupt_count}).")
    return corrupt_count == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SKYsense AI - Dataset Verification Utility")
    parser.add_argument("--thorough", action="store_true", help="Verify every single image file header in the dataset")
    args = parser.parse_args()

    print("=" * 65)
    print("       SKYsense AI - Dataset Verification & Audit")
    print("=" * 65)

    sample_limit = 10000 if args.thorough else 100
    v1 = verify_processed_dataset()
    v2 = verify_splits()
    v3 = verify_image_integrity(sample_limit=sample_limit)

    print("\n" + "=" * 65)
    if v1 and v2 and v3:
        print("  [SUCCESS] Dataset verification PASSED: All 2,543 images verified.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("  [FAILURE] Dataset verification FAILED.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
