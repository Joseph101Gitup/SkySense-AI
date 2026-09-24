#!/usr/bin/env python
"""
SKYsense AI - Automated Test Suite Runner Script
Runs all automated unit, integration, and security tests across the SKYsense platform.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "05_Backend"
MANAGE_PY = BACKEND_DIR / "manage.py"


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Run Automated Tests")
    parser.add_argument("--module", type=str, default="", help="Specific test module to run (e.g. tests.test_14_security_hardening)")
    parser.add_argument("--failfast", action="store_true", help="Stop on first test failure")
    parser.add_argument("--verbosity", type=int, default=2, help="Verbosity level (1, 2, or 3). Default: 2")
    args = parser.parse_args()

    print("=" * 65)
    print("       SKYsense AI - Automated Test Suite Runner")
    print("=" * 65 + "\n")

    target = args.module if args.module else "tests"

    cmd = [
        sys.executable,
        str(MANAGE_PY),
        "test",
        target,
        f"--verbosity={args.verbosity}",
    ]
    if args.failfast:
        cmd.append("--failfast")

    print(f"[+] Executing: {' '.join(cmd)}\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    res = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)

    print("\n" + "=" * 65)
    if res.returncode == 0:
        print("  [SUCCESS] All automated tests passed successfully.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("  [FAILURE] One or more automated tests failed.")
        print("=" * 65)
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
