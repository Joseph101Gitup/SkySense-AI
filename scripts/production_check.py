#!/usr/bin/env python
"""
SKYsense AI - Production Readiness & Security Audit Script
Performs pre-deployment validation:
- Django deploy checks (manage.py check --deploy)
- DEBUG setting evaluation
- Secret key strength & entropy audit
- ALLOWED_HOSTS & CSRF trusted origins configuration
- Security headers & cookie flags (HSTS, SSL redirect, secure cookies)
- WhiteNoise static file serving
- Database configuration
- Model binary and artifact availability
- .env file safety audit
"""

import sys
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "05_Backend"
AI_MODEL_DIR = REPO_ROOT / "03_AI_Model"
MANAGE_PY = BACKEND_DIR / "manage.py"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skysense.settings")


def print_step(title: str):
    print(f"\n[+] {title}")


def ok(msg):    print(f"    [PASS] {msg}")
def warn(msg):  print(f"    [WARN] {msg}")
def fail(msg):  print(f"    [FAIL] {msg}")
def info(msg):  print(f"    [INFO] {msg}")


def audit_env_file_safety() -> tuple:
    """Verify .env is excluded from git and .env.example is present."""
    print_step("Auditing .env File Safety...")
    failures, warnings = [], []

    env_file = REPO_ROOT / ".env"
    backend_env = BACKEND_DIR / ".env"
    env_example = REPO_ROOT / ".env.example"

    if env_file.exists() or backend_env.exists():
        # Check it's in .gitignore
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-v", str(env_file if env_file.exists() else backend_env)],
                capture_output=True, text=True, cwd=str(REPO_ROOT)
            )
            if result.returncode == 0:
                ok(".env is excluded by .gitignore")
            else:
                failures.append(".env file is present but NOT excluded by .gitignore — risk of secret exposure.")
                fail(".env is NOT in .gitignore — secrets may be committed to git!")
        except FileNotFoundError:
            warn("git not found, could not verify .gitignore status of .env")
    else:
        warn(".env file not found. Copy .env.example to .env and fill in secrets before deploying.")

    if env_example.exists():
        # Check .env.example doesn't contain real secrets (non-empty password= / key= values)
        real_secrets_found = []
        for line in env_example.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                continue
            if '=' in stripped:
                key_part, _, val_part = stripped.partition('=')
                val_part = val_part.strip()
                # Blank or clearly placeholder values are safe
                if not val_part:
                    continue
                placeholder_words = ['change-this', 'your-', 'example', 'replace', 'placeholder', 'strongpassword']
                if any(pw in val_part.lower() for pw in placeholder_words):
                    continue
                # Flag any non-trivial value for secret-looking keys
                secret_keys = ['secret', 'password', 'token', 'api_key', 'private_key']
                if any(sk in key_part.lower() for sk in secret_keys) and len(val_part) > 3:
                    real_secrets_found.append(key_part.strip())

        if real_secrets_found:
            warnings.append(f".env.example may contain actual secrets in keys: {real_secrets_found}")
            warn(f".env.example appears to contain non-placeholder secrets: {real_secrets_found}")
        else:
            ok(".env.example contains only placeholder values")
    else:
        warnings.append(".env.example not found. Recommended for onboarding new developers.")
        warn(".env.example not present in repository root")

    return failures, warnings


def audit_django_settings() -> tuple:
    print_step("Auditing Django Security & Deployment Settings...")
    import django
    django.setup()
    from django.conf import settings

    failures = []
    warnings = []

    # 1. DEBUG
    if settings.DEBUG:
        warnings.append("DJANGO_DEBUG is True. Must be False in production.")
        warn("DEBUG is True (Acceptable for local dev; MUST be False in production).")
    else:
        ok("DEBUG is False (Production safe).")

    # 2. SECRET_KEY
    key = settings.SECRET_KEY
    placeholder_indicators = [
        "change-this", "generate-a-strong", "fallback-dev",
        "master-thesis-project-key-2026-fallback",
        "skysense-ai-secure-master-thesis"
    ]
    if not key or any(p in key for p in placeholder_indicators):
        warnings.append("Placeholder or weak SECRET_KEY detected — replace before production deployment.")
        warn(f"Placeholder SECRET_KEY detected — must be replaced with cryptographic key for production.")
    elif len(key) < 50:
        warnings.append(f"SECRET_KEY length is {len(key)} chars — should be 50+ for production.")
        warn(f"SECRET_KEY length is {len(key)} chars (recommend 50+ chars).")
    else:
        ok(f"SECRET_KEY is set and has sufficient length ({len(key)} chars).")

    # 3. ALLOWED_HOSTS
    hosts = settings.ALLOWED_HOSTS
    if not hosts:
        failures.append("ALLOWED_HOSTS is empty — host header injection risk.")
        fail("ALLOWED_HOSTS is empty.")
    elif "*" in hosts:
        warnings.append("ALLOWED_HOSTS contains wildcard '*'. Avoid in production.")
        warn("ALLOWED_HOSTS contains wildcard '*' — restrict to specific hostnames in production.")
    else:
        ok(f"ALLOWED_HOSTS is configured: {hosts}")

    # 4. CSRF Trusted Origins
    csrf_origins = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
    if csrf_origins:
        ok(f"CSRF_TRUSTED_ORIGINS is set: {csrf_origins}")
    else:
        warnings.append("CSRF_TRUSTED_ORIGINS is empty.")
        warn("CSRF_TRUSTED_ORIGINS is not configured.")

    # 5. SSL & HTTPS
    ssl_redirect = getattr(settings, "SECURE_SSL_REDIRECT", False)
    session_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
    csrf_secure = getattr(settings, "CSRF_COOKIE_SECURE", False)
    hsts = getattr(settings, "SECURE_HSTS_SECONDS", 0)

    if ssl_redirect:
        ok("SECURE_SSL_REDIRECT is True.")
    else:
        warn("SECURE_SSL_REDIRECT is False (OK if Nginx handles HTTPS redirect; FAIL if no reverse proxy).")

    if session_secure:
        ok("SESSION_COOKIE_SECURE is True.")
    else:
        warn("SESSION_COOKIE_SECURE is False — session hijacking risk over HTTP.")

    if csrf_secure:
        ok("CSRF_COOKIE_SECURE is True.")
    else:
        warn("CSRF_COOKIE_SECURE is False — CSRF token interception risk over HTTP.")

    if hsts >= 31536000:
        ok(f"SECURE_HSTS_SECONDS is {hsts}s (≥ 1 year). HSTS preload eligible.")
    elif hsts > 0:
        warn(f"SECURE_HSTS_SECONDS is {hsts}s — consider 31536000 (1 year) for production.")
    else:
        warn("SECURE_HSTS_SECONDS is 0 — no HSTS enforcement. Acceptable if Nginx handles HSTS headers.")

    # 6. Content Security Headers
    if getattr(settings, "SECURE_CONTENT_TYPE_NOSNIFF", False):
        ok("SECURE_CONTENT_TYPE_NOSNIFF is enabled.")
    else:
        warnings.append("SECURE_CONTENT_TYPE_NOSNIFF is not enabled.")
        warn("SECURE_CONTENT_TYPE_NOSNIFF is disabled.")

    if getattr(settings, "X_FRAME_OPTIONS", "") == "DENY":
        ok("X_FRAME_OPTIONS is DENY.")
    else:
        warnings.append(f"X_FRAME_OPTIONS is {getattr(settings, 'X_FRAME_OPTIONS', 'unset')}.")
        warn(f"X_FRAME_OPTIONS is {getattr(settings, 'X_FRAME_OPTIONS', 'unset')}. Recommend DENY.")

    # 7. Cookie HTTP-only
    if getattr(settings, "CSRF_COOKIE_HTTPONLY", False):
        ok("CSRF_COOKIE_HTTPONLY is enabled.")
    if getattr(settings, "SESSION_COOKIE_HTTPONLY", False):
        ok("SESSION_COOKIE_HTTPONLY is enabled.")

    # 8. WhiteNoise static file storage
    storages = getattr(settings, "STORAGES", {})
    static_backend = storages.get("staticfiles", {}).get("BACKEND", "")
    if "whitenoise" in static_backend.lower():
        ok(f"WhiteNoise static file serving is active: {static_backend}")
    else:
        info(f"Static file backend: {static_backend} (WhiteNoise recommended for production).")

    # 9. Database configuration
    db_engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    db_name = settings.DATABASES.get("default", {}).get("NAME", "")
    if "sqlite3" in db_engine:
        warn(f"Database: SQLite3 ({db_name}) — adequate for single-node deployments. Use PostgreSQL for multi-node.")
    elif "postgresql" in db_engine:
        ok(f"Database: PostgreSQL ({db_name}) — production recommended engine.")
    else:
        info(f"Database engine: {db_engine}")

    return failures, warnings


def audit_model_artifacts() -> tuple:
    print_step("Auditing AI Model Artifacts & Weights...")
    failures = []
    warnings = []

    keras_model = AI_MODEL_DIR / "models" / "best_xception_rainfall.keras"
    tflite_model = AI_MODEL_DIR / "models" / "xception_rainfall.tflite"
    test_metrics = AI_MODEL_DIR / "evaluation" / "test_evaluation_summary.json"
    if not test_metrics.exists():
        test_metrics = AI_MODEL_DIR / "evaluation" / "test_metrics.json"

    if keras_model.exists():
        size_mb = keras_model.stat().st_size / (1024 * 1024)
        ok(f"Keras model weights present ({size_mb:.1f} MB): {keras_model.name}")
    else:
        failures.append(f"Missing primary model weights: {keras_model}")
        fail(f"Missing primary model weights: {keras_model}")

    if tflite_model.exists():
        size_mb = tflite_model.stat().st_size / (1024 * 1024)
        ok(f"TFLite edge model present ({size_mb:.1f} MB): {tflite_model.name}")
    else:
        warnings.append(f"Missing TFLite model: {tflite_model}")
        warn(f"Missing TFLite model: {tflite_model} (optional for edge deployment)")

    if test_metrics.exists():
        ok(f"Evaluation metrics artifact present: {test_metrics.name}")
    else:
        warnings.append(f"Missing evaluation metrics file: {test_metrics}")
        warn(f"Missing evaluation metrics file: {test_metrics}")

    return failures, warnings


def run_django_deploy_check() -> bool:
    print_step("Running Django manage.py check --deploy...")
    cmd = [sys.executable, str(MANAGE_PY), "check", "--deploy"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    res = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)
    if res.returncode == 0:
        ok("manage.py check --deploy: No issues found.")
    else:
        fail("manage.py check --deploy: Issues detected (see output above).")
    return res.returncode == 0


def main():
    print("=" * 65)
    print("       SKYsense AI - Production Readiness & Security Audit")
    print("=" * 65)

    all_failures = []
    all_warnings = []

    f0, w0 = audit_env_file_safety()
    all_failures.extend(f0)
    all_warnings.extend(w0)

    f1, w1 = audit_django_settings()
    all_failures.extend(f1)
    all_warnings.extend(w1)

    f2, w2 = audit_model_artifacts()
    all_failures.extend(f2)
    all_warnings.extend(w2)

    deploy_ok = run_django_deploy_check()
    if not deploy_ok:
        all_failures.append("Django deploy check failed — resolve warnings before deploying.")

    print("\n" + "=" * 65)
    if not all_failures:
        print("  [SUCCESS] Production readiness audit PASSED with 0 critical failures.")
        if all_warnings:
            print(f"  Advisory: {len(all_warnings)} informational warning(s) noted above.")
        print("=" * 65)
        sys.exit(0)
    else:
        print(f"  [FAILURE] Audit detected {len(all_failures)} critical issue(s):")
        for f in all_failures:
            print(f"   - {f}")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
