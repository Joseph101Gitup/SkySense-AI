#!/usr/bin/env python
"""
SKYsense AI - Django Development Server Automation Script
Starts the ASGI/WSGI local server, verifies host binding, and provides quick navigation URLs.
Supports --check-only for continuous integration or non-interactive validation.
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
    parser = argparse.ArgumentParser(description="SKYsense AI - Start Django Development Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Binding IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--check-only", action="store_true", help="Run system check without binding server port")
    args = parser.parse_args()

    print("=" * 65)
    print("       SKYsense AI - Web Platform Server")
    print("=" * 65)
    print(f"  Target Binding : http://{args.host}:{args.port}/")
    print(f"  Dashboard      : http://{args.host}:{args.port}/dashboard/")
    print(f"  API Ingestion  : http://{args.host}:{args.port}/api/predict/")
    print("=" * 65 + "\n")

    if not MANAGE_PY.exists():
        print(f"[!] Error: manage.py not found at {MANAGE_PY}")
        sys.exit(1)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    if args.check_only:
        print("[+] Running Django system pre-flight checks...")
        cmd = [sys.executable, str(MANAGE_PY), "check"]
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)
        if res.returncode == 0:
            print("\n  [SUCCESS] Server configuration is valid.")
            sys.exit(0)
        else:
            print("\n  [!] Pre-flight checks failed.")
            sys.exit(res.returncode)

    print(f"[+] Starting development server on {args.host}:{args.port}...")
    print("    Press Ctrl+C to terminate server.\n")
    cmd = [sys.executable, str(MANAGE_PY), "runserver", f"{args.host}:{args.port}"]
    try:
        subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)
    except KeyboardInterrupt:
        print("\n[+] Server terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
