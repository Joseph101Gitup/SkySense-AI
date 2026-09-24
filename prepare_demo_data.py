#!/usr/bin/env python
"""
SKYsense AI - Demo Data Preparation Utility (Root Entrypoint)
Delegates to scripts/prepare_demo_data.py.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import prepare_demo_data

if __name__ == "__main__":
    prepare_demo_data.main()
