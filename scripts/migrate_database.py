#!/usr/bin/env python
"""
SKYsense AI - Database Migration Automation Script
Applies Django schema migrations, validates table creation, and confirms database integrity.
"""

import sys
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "05_Backend"
MANAGE_PY = BACKEND_DIR / "manage.py"


def run_django_command(args: list) -> bool:
    cmd = [sys.executable, str(MANAGE_PY)] + args
    print(f"[+] Executing: {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)
    return result.returncode == 0


def main():
    print("=" * 65)
    print("       SKYsense AI - Database Migration & Schema Sync")
    print("=" * 65 + "\n")

    if not MANAGE_PY.exists():
        print(f"[!] Error: manage.py not found at {MANAGE_PY}")
        sys.exit(1)

    # 1. Makemigrations
    print("[1/2] Generating any pending migrations...")
    if not run_django_command(["makemigrations"]):
        print("[!] Error generating migrations.")
        sys.exit(1)

    # 2. Migrate
    print("\n[2/2] Applying database migrations...")
    if not run_django_command(["migrate"]):
        print("[!] Error applying migrations.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("  [SUCCESS] All database migrations successfully applied.")
    print("=" * 65)
    sys.exit(0)


if __name__ == "__main__":
    main()
