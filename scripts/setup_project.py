#!/usr/bin/env python
"""
SKYsense AI - Automated Environment & Project Setup Script
Validates Python runtime, initializes configuration (.env), ensures directories,
and verifies required core packages. Cross-platform & Windows compatible.
"""

import sys
import os
import shutil
import secrets
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "05_Backend"
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"

REQUIRED_DIRS = [
    BACKEND_DIR / "media" / "predictions",
    BACKEND_DIR / "staticfiles",
    AI_MODEL_DIR / "models",
    AI_MODEL_DIR / "evaluation",
    AI_MODEL_DIR / "datasets" / "raw",
    AI_MODEL_DIR / "datasets" / "processed",
    AI_MODEL_DIR / "datasets" / "splits",
    REPO_ROOT / "15_Logs",
]

CORE_PACKAGES = [
    ("django", "Django"),
    ("PIL", "Pillow"),
    ("tensorflow", "TensorFlow"),
    ("numpy", "NumPy"),
    ("matplotlib", "Matplotlib"),
]


def print_step(title: str):
    print(f"\n[+] {title}")


def check_python_version() -> bool:
    print_step("Checking Python Runtime...")
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"    Detected Python version: {major}.{minor}.{sys.version_info.micro} ({sys.executable})")
    if major < 3 or (major == 3 and minor < 10):
        print(f"    [!] Error: Python 3.10 or higher is required. Found: {major}.{minor}")
        return False
    print("    [OK] Python version meets specifications (>= 3.10).")
    return True


def setup_env_file() -> bool:
    print_step("Checking Environment Configuration (.env)...")
    env_file = REPO_ROOT / ".env"
    env_example = REPO_ROOT / ".env.example"

    if env_file.exists():
        print(f"    [OK] Active .env file found at: {env_file}")
        return True

    if not env_example.exists():
        print(f"    [!] Error: Template {env_example} not found.")
        return False

    print("    Creating .env file from .env.example with secure random secret key...")
    content = env_example.read_text(encoding="utf-8")
    generated_key = secrets.token_urlsafe(50)
    content = content.replace("generate-a-strong-random-50-character-secret-key-here", generated_key)
    env_file.write_text(content, encoding="utf-8")
    print(f"    [OK] Created .env with generated SECRET_KEY at: {env_file}")
    return True


def ensure_directories() -> bool:
    print_step("Ensuring Storage and Media Directories...")
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"    [OK] Directory verified: {directory.relative_to(REPO_ROOT)}")
    return True


def verify_packages() -> bool:
    print_step("Verifying Core Package Dependencies...")
    all_ok = True
    for module_name, display_name in CORE_PACKAGES:
        try:
            mod = __import__(module_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"    [OK] {display_name:<15} : v{ver}")
        except ImportError:
            print(f"    [!] MISSING: {display_name:<15} (module: '{module_name}')")
            all_ok = False
    return all_ok


def main():
    print("=" * 65)
    print("       SKYsense AI - Project Environment Setup")
    print("=" * 65)

    success = True
    success = check_python_version() and success
    success = setup_env_file() and success
    success = ensure_directories() and success
    success = verify_packages() and success

    print("\n" + "=" * 65)
    if success:
        print("  [SUCCESS] SKYsense AI project environment is fully prepared.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("  [WARNING] Some requirements or packages are missing.")
        print("            Please install requirements in your virtual environment.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
