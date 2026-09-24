#!/usr/bin/env python
"""
Standalone automated test runner for SKYsense AI.
Executes the full automated test suite directly from project root.

Usage:
    python tests/run_all_tests.py
    python tests/run_all_tests.py --suite=tests
"""

import os
import sys
import argparse
from pathlib import Path

# Resolve directory roots
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "05_Backend"
AI_MODEL_DIR = PROJECT_ROOT / "03_AI_Model"

for directory in [str(BACKEND_DIR), str(AI_MODEL_DIR)]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skysense.settings")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import django
from django.conf import settings
from django.core.management import call_command


def run_tests(test_labels=None, verbosity=2):
    """Initializes Django and runs test suite."""
    os.chdir(str(BACKEND_DIR))
    django.setup()

    if not test_labels:
        test_labels = ['tests']

    print("=" * 70)
    print("SKYsense AI - Automated Test Suite Runner")
    print(f"Target Labels: {test_labels}")
    print("=" * 70)

    try:
        call_command('test', *test_labels, verbosity=verbosity, interactive=False)
        print("\n[SUCCESS] All automated tests completed successfully!")
        sys.exit(0)
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        print(f"\n[ERROR] Test run encountered error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SKYsense AI Automated Test Suite Runner")
    parser.add_argument(
        "--suite",
        dest="suite",
        default="tests",
        help="Test target (default: 'tests', or 'all' to include app tests)"
    )
    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        default=2,
        help="Verbosity level (1, 2, or 3)"
    )
    args = parser.parse_args()

    targets = None if args.suite == "all" else [args.suite]
    run_tests(targets, verbosity=args.verbosity)
