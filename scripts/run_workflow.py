#!/usr/bin/env python
"""
SKYsense AI - Complete Development Workflow Orchestrator
Executes the unified engineering workflow:
  VERIFY -> TRAIN -> EVALUATE -> EXPORT MODEL -> RUN MIGRATIONS -> START DJANGO -> TEST APPLICATION
"""

import sys
import os
import time
import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def print_banner(step_num: int, total_steps: int, title: str):
    print("\n" + "=" * 70)
    print(f"  STEP [{step_num}/{total_steps}]: {title}")
    print("=" * 70)


def execute_step(script_name: str, args: list = None) -> bool:
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])
    start_time = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env)
    elapsed = time.time() - start_time
    if result.returncode == 0:
        print(f"\n[OK] Step '{script_name}' completed successfully in {elapsed:.1f}s.")
        return True
    else:
        print(f"\n[!] ERROR: Step '{script_name}' failed with exit code {result.returncode} ({elapsed:.1f}s).")
        return False


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Full Workflow Orchestration Runner")
    parser.add_argument("--skip-train", action="store_true",
                        help="Skip model training if validated checkpoint already exists")
    parser.add_argument("--train-dry-run", action="store_true",
                        help="Run quick 1-epoch training smoke test instead of full training")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Skip automated test execution")
    args = parser.parse_args()

    total_steps = 7
    current_step = 1

    print("\n" + "#" * 70)
    print("         SKYSENSE AI - UNIFIED DEVELOPMENT PIPELINE")
    print("         VERIFY -> TRAIN -> EVALUATE -> EXPORT -> MIGRATE -> SERVER -> TEST")
    print("#" * 70)

    # 1. SETUP & VERIFY
    print_banner(current_step, total_steps, "VERIFY (Dataset Integrity & Environment)")
    if not execute_step("setup_project.py"):
        sys.exit(1)
    if not execute_step("verify_dataset.py"):
        sys.exit(1)
    current_step += 1

    # 2. TRAIN
    print_banner(current_step, total_steps, "TRAIN (Two-Phase Transfer Learning CNN)")
    if args.skip_train:
        print("    [INFO] --skip-train specified. Skipping training phase and using existing checkpoint.")
    else:
        train_args = ["--dry-run"] if args.train_dry_run else []
        if not execute_step("train_model.py", train_args):
            sys.exit(1)
    current_step += 1

    # 3. EVALUATE
    print_banner(current_step, total_steps, "EVALUATE (Held-out Test Partition & Confusion Matrix)")
    if not execute_step("evaluate_model.py"):
        sys.exit(1)
    current_step += 1

    # 4. EXPORT MODEL
    print_banner(current_step, total_steps, "EXPORT MODEL (TensorFlow Lite Edge & IoT Deployment)")
    if not execute_step("export_model.py"):
        sys.exit(1)
    current_step += 1

    # 5. RUN MIGRATIONS
    print_banner(current_step, total_steps, "RUN MIGRATIONS (Database Schema Synchronization)")
    if not execute_step("migrate_database.py"):
        sys.exit(1)
    current_step += 1

    # 6. START DJANGO
    print_banner(current_step, total_steps, "START DJANGO (Server Pre-Flight & Health Checks)")
    if not execute_step("start_server.py", ["--check-only"]):
        sys.exit(1)
    current_step += 1

    # 7. TEST APPLICATION & AUDIT
    print_banner(current_step, total_steps, "TEST APPLICATION (Automated Security & Unit Test Suite)")
    if not args.skip_tests:
        if not execute_step("run_tests.py"):
            sys.exit(1)
    if not execute_step("production_check.py"):
        sys.exit(1)

    print("\n" + "#" * 70)
    print("  [SUCCESS] All pipeline stages completed successfully!")
    print("  Ready for local development or production deployment.")
    print("#" * 70 + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
