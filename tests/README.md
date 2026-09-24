# SKYsense AI — Automated Test Suite

## Overview
This directory provides comprehensive, end-to-end automated testing for **SKYsense AI**, covering all architectural tiers from application bootstrap, UI routing, security guards, deep learning inference, SQLite persistence, history auditing, to programmatic IoT API ingestion.

---

## 13 Test Categories & Architecture Matrix

| # | Test Suite | File | Focus Areas & Invariants Verified |
|---|---|---|---|
| **1** | **Django Application Loads** | `tests/test_01_django_app_loads.py` | Settings initialization, `SECRET_KEY`, SQLite connection, App registry (`core`, `predictions`, `accounts`), WSGI and ASGI handlers. |
| **2** | **Home Page** | `tests/test_02_home_page.py` | Status 200 OK, `landing.html` template, Hero title & CTA buttons, 5 operational pipeline stages, 4 AI capabilities, 7 tech stack components, Research pillars, Future IoT Architecture with explicit **Future Work** banner, footer branding. |
| **3** | **Login** | `tests/test_03_login.py` | Form rendering, valid credential login & redirect to `/dashboard/`, session creation, invalid password rejection, nonexistent user handling, `?next=` query parameter redirects, logout termination. |
| **4** | **Registration** | `tests/test_04_registration.py` | Account creation, **native PBKDF2 password hashing** (`pbkdf2_sha256$`), zero plaintext storage, session establishment, password confirmation mismatch detection, duplicate username rejection. |
| **5** | **Authentication Protection** | `tests/test_05_auth_protection.py` | `@login_required` guards on `/dashboard/`, `/predict/`, `/history/`, `/profile/`. Cross-user data isolation: User A cannot view or delete User B's predictions (403 Forbidden). Superuser/staff administrative visibility. |
| **6** | **Prediction Model** | `tests/test_06_prediction_model.py` | `Prediction` ORM model, UUID primary keys, choices (`RainfallClass`, `SourceType`), `clean()` probability summation check (~1.0), confidence range [0.0, 1.0], paired coordinate enforcement, helper properties (`prob_low_pct`, `latency_ms`, etc.). |
| **7** | **Image Upload Validation** | `tests/test_07_image_upload_validation.py` | `ImagePredictionForm` validation, valid JPEG and PNG acceptance, missing file rejection, oversized file rejection (>15 MB ceiling), empty POST rejection. |
| **8** | **AI Inference** | `tests/test_08_ai_inference.py` | `RainfallInferenceService` singleton pattern (`get_instance()`), image preprocessing into normalized 256×256 float32 tensor [0.0, 1.0], execution returning valid classes, confidence scores, and Softmax distributions summing to 1.0. |
| **9** | **Prediction Database Creation** | `tests/test_09_prediction_database_creation.py` | `process_image_prediction` pipeline, SQLite record persistence, UUID generation, timestamps, user linking, edge IoT metadata fields (`device_id`, `latitude`, `longitude`, `temperature`, `humidity`), meteorological advisories. |
| **10** | **Prediction History** | `tests/test_10_prediction_history.py` | `/history/` rendering, pagination (10 items/page), query search (`?q=`), category filtering (`?class=`), date range filtering, sort order (`?sort=newest` vs `?sort=oldest`), detail view (`/history/<uuid>/`), safe deletion with filesystem cleanup. |
| **11** | **API Endpoint** | `tests/test_11_api_endpoint.py` | `POST /api/predict/` with `multipart/form-data`, `@csrf_exempt` accessibility for edge nodes, structured JSON response, IoT metadata persistence and echoing, missing `image` 400 error, HTTP GET 405 error, paired coordinate validation, sensor range checks. |
| **12** | **Invalid Image Handling** | `tests/test_12_invalid_image_handling.py` | Rejecting text/binary disguise files renamed as `.jpg` without crashing or exposing stack traces (400 Bad Request), rejecting 0-byte files, handling corrupted/truncated JPEG streams, verifying `CorruptedImageError`. |
| **13** | **Unsupported File Handling** | `tests/test_13_unsupported_file_handling.py` | Rejecting `.exe`, `.pdf`, `.txt`, `.mp4`, `.zip`, `.svg` with clean error messages in both web upload forms and the REST API endpoint. |

---

## Running the Automated Tests

### Method 1: Using Django's Test Runner (Recommended)
From the `05_Backend` directory:
```bash
# Run all 13 test suites (69 tests)
python manage.py test tests

# Run all tests across the entire project (106 tests)
python manage.py test

# Run a specific test suite (e.g., API endpoint tests)
python manage.py test tests.test_11_api_endpoint
```

### Method 2: Using the Root Test Runner
From the repository root:
```bash
# Run all 13 test suites
python tests/run_all_tests.py

# Run all project tests with high verbosity
python tests/run_all_tests.py --suite=all -v 2
```

---

## Hardware Status Disclaimer
> [!IMPORTANT]
> **Physical IoT hardware is NOT currently implemented or deployed.**
> All edge device test cases and simulator scripts validate the **software communication interface** using synthetic payloads.
