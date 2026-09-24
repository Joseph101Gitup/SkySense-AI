#!/usr/bin/env python
"""
SKYsense AI - Demo Data Preparation Utility
Selects a representative set of actual photographic cloud specimens from the dataset,
copies them into demo_images/ organized by category:
  demo_images/
    low_medium/
    medium_heavy/
    no_low/
Preserves source metadata and ground-truth labels in demo_images/labels.json.
Does NOT generate fake predictions; preserves actual image bytes and source provenance.
"""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"
DEMO_DIR = REPO_ROOT / "demo_images"

# Category mapping: Target Folder -> (Formal Class Code, Display Name, Source Folders)
CATEGORY_MAPPING = {
    "low_medium": {
        "class_code": "Low_to_Medium_Rain",
        "display_name": "Low to Medium Rain",
        "description": "Stratiform & layered cloud formations associated with light-to-moderate rain.",
        "preferred_genera": ["As", "Ns", "St", "Sc"],  # Altostratus, Nimbostratus, Stratus, Stratocumulus
    },
    "medium_heavy": {
        "class_code": "Medium_to_Heavy_Rain",
        "display_name": "Medium to Heavy Rain",
        "description": "Convective & vertically developed cloud regimes associated with heavy rain / storms.",
        "preferred_genera": ["Cb", "Cu", "Ac"],  # Cumulonimbus, Cumulus congestus
    },
    "no_low": {
        "class_code": "No_to_Low_Rain",
        "display_name": "No to Low Rain",
        "description": "High-altitude or detached fair-weather cloud formations with minimal rain probability.",
        "preferred_genera": ["Ci", "Cc", "Cs", "Ct"],  # Cirrus, Cirrocumulus, Cirrostratus, Contrails
    },
}

GENUS_NAMES = {
    "Ci": "Cirrus (Ci)",
    "Cs": "Cirrostratus (Cs)",
    "Cc": "Cirrocumulus (Cc)",
    "Ac": "Altocumulus (Ac)",
    "As": "Altostratus (As)",
    "Sc": "Stratocumulus (Sc)",
    "St": "Stratus (St)",
    "Ns": "Nimbostratus (Ns)",
    "Cb": "Cumulonimbus (Cb)",
    "Cu": "Cumulus (Cu)",
    "Ct": "Contrails (Ct)",
}


def find_source_images(class_code: str, count: int, preferred_genera: list) -> list:
    """
    Finds actual dataset images from test split (or processed split)
    trying to sample across diverse cloud genera.
    """
    candidate_dirs = [
        AI_MODEL_DIR / "datasets" / "splits" / "test" / class_code,
        AI_MODEL_DIR / "datasets" / "processed" / class_code,
    ]

    source_dir = None
    for d in candidate_dirs:
        if d.exists() and any(d.glob("*.jpg")):
            source_dir = d
            break

    if not source_dir:
        return []

    all_files = sorted(list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.png")))
    selected = []

    # Try selecting one from each preferred genus first
    for genus in preferred_genera:
        prefix = f"{genus}_"
        match = next((f for f in all_files if f.name.startswith(prefix) and f not in selected), None)
        if match:
            selected.append(match)
        if len(selected) >= count:
            break

    # If still need more, fill from remaining files
    if len(selected) < count:
        for f in all_files:
            if f not in selected:
                selected.append(f)
            if len(selected) >= count:
                break

    return selected


def prepare_demo_data(samples_per_class: int = 4, force: bool = False) -> bool:
    print("=" * 68)
    print("         SKYsense AI - Demo Data Preparation Utility")
    print("=" * 68)
    print(f"  Target Destination : {DEMO_DIR}")
    print(f"  Samples Per Class  : {samples_per_class}")
    print("=" * 68 + "\n")

    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "dataset_name": "CCSN Database (Cirrus Cumulus Stratus Nimbus)",
        "source_dataset_url": "https://www.kaggle.com/datasets/mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database",
        "description": "Representative actual photographic specimens sampled from verified test partitions for live demonstration. No synthetic or fake predictions are generated.",
        "is_sample_dataset_images": True,
        "total_samples": 0,
        "samples": []
    }

    total_copied = 0

    for cat_folder, info in CATEGORY_MAPPING.items():
        cat_dir = DEMO_DIR / cat_folder
        cat_dir.mkdir(parents=True, exist_ok=True)

        class_code = info["class_code"]
        display_name = info["display_name"]
        preferred = info["preferred_genera"]

        print(f"[+] Sampling '{display_name}' (target: {cat_folder}/)...")

        source_files = find_source_images(class_code, samples_per_class, preferred)
        if not source_files:
            print(f"    [!] Error: No source images found for {class_code}")
            return False

        for src_path in source_files:
            dest_path = cat_dir / src_path.name
            shutil.copy2(src_path, dest_path)

            # Verify integrity with PIL
            with Image.open(dest_path) as im:
                im.verify()
                width, height = im.size
                format_name = im.format

            # Extract cloud genus prefix (e.g. 'As', 'Cb', 'Ci')
            genus_code = src_path.name.split('_')[0] if '_' in src_path.name else "Cloud"
            genus_name = GENUS_NAMES.get(genus_code, f"{genus_code} Cloud")

            sample_entry = {
                "filename": src_path.name,
                "relative_path": f"demo_images/{cat_folder}/{src_path.name}",
                "category_key": cat_folder,
                "category_code": class_code,
                "category_label": display_name,
                "cloud_genus_code": genus_code,
                "cloud_genus": genus_name,
                "resolution": f"{width}x{height}",
                "format": format_name,
                "size_bytes": dest_path.stat().st_size,
                "provenance": f"Verified specimen from {class_code} test partition",
                "is_sample_dataset_image": True
            }
            manifest["samples"].append(sample_entry)
            total_copied += 1
            print(f"    [OK] Copied {src_path.name:<22} -> {genus_name:<20} ({width}x{height})")

    manifest["total_samples"] = total_copied

    # 1. Save JSON manifest
    labels_file = DEMO_DIR / "labels.json"
    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[+] Saved source labels manifest: {labels_file.relative_to(REPO_ROOT)}")

    # 2. Save Markdown documentation
    readme_file = DEMO_DIR / "README.md"
    readme_content = f"""# SKYsense AI: Demonstration Cloud Specimens

This directory contains representative, unmanipulated cloud images selected from the verified dataset splits for demonstration purposes and live inference testing.

> **Notice:** These are authentic research specimens from the CCSN cloud database. No fake predictions or artificial outputs are stored. The web application dynamically runs deep learning inference when any sample is analyzed.

## Directory Structure

```text
demo_images/
├── labels.json           # Machine-readable ground truth labels and specimen metadata
├── low_medium/           # Stratus, Altostratus, Nimbostratus specimens ({samples_per_class} images)
├── medium_heavy/         # Cumulonimbus, Towering Cumulus specimens ({samples_per_class} images)
└── no_low/               # Cirrus, Altocumulus, Contrail specimens ({samples_per_class} images)
```

## Summary of Demonstration Specimens

| Category | Category Label | Cloud Genus | Filename | Resolution |
| :--- | :--- | :--- | :--- | :--- |
"""
    for s in manifest["samples"]:
        readme_content += f"| `{s['category_key']}` | {s['category_label']} | {s['cloud_genus']} | `{s['filename']}` | {s['resolution']} |\n"

    readme_content += "\n*Total specimens: " + str(total_copied) + "*\n"
    readme_file.write_text(readme_content, encoding="utf-8")
    print(f"[+] Saved documentation: {readme_file.relative_to(REPO_ROOT)}")

    print("\n" + "=" * 68)
    print(f"  [SUCCESS] Demo data preparation complete: {total_copied} specimens ready.")
    print("=" * 68)
    return True


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Prepare Demo Dataset Images")
    parser.add_argument("--samples-per-class", type=int, default=4,
                        help="Number of representative specimens to copy per category (default: 4)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing demo_images directory")
    args = parser.parse_args()

    success = prepare_demo_data(samples_per_class=args.samples_per_class, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
