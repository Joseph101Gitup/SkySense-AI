# SkySense AI Development Journal

## Day 1

Date: Initial Setup
Hours Worked: 6
Today's Goal: Project setup, architecture audit, dataset verification.
Tasks Completed:
- Audited repository and original Jupyter notebook.
- Verified 2,543 images across 3 rainfall likelihood categories.
- Resolved scientific ambiguity regarding 11 WMO cloud genus classes vs 3 target rainfall categories.

## Day 2

Goal: Clean AI Pipeline Implementation & Evaluation
Completed:
- Built isolated Python 3.11 environment with TensorFlow 2.19.
- Created reproducible stratified splitting pipeline (70% train, 15% val, 15% test; seed 42).
- Verified disjoint sets (Train ∩ Val = 0, Train ∩ Test = 0, Val ∩ Test = 0).
- Implemented pure-NumPy evaluation metrics bypassing Windows DLL security blocks.
- Trained Xception model with frozen backbone + fine-tuning callbacks.
- Checkpointed best model (`best_xception_rainfall.keras`, 84 MB) and exported edge TFLite (`xception_rainfall.tflite`, 20.55 MB).
- Achieved 58.27% accuracy, 0.9103 loss, and 56.60% macro F1 on the independent 381-image test set.

## Day 3

Goal: Standalone Production AI Inference Service
Completed:
- Created `03_AI_Model/src/inference.py` singleton service.
- Implemented robust input validation (file size <15MB, valid formats JPG/PNG, corruption checks).
- Implemented normalized probability breakdown matching `{ predicted_class, confidence, probabilities }`.
- Verified with 7 standalone unit tests (`test_inference.py`).
- Added CLI interface `predict.py <image_path>`.

## Day 4

Goal: SkySenseWeb Django Web Application
Completed:
- Initialized Django 5 project at `05_Backend/` with apps: `core`, `predictions`, `accounts`.
- Bridged `predictions/services.py` to `03_AI_Model.src.inference` (zero duplicate prediction logic).
- Designed and implemented 9 responsive, master's-project-quality pages:
  1. Landing Page (`/`)
  2. Dashboard with Chart.js analytics (`/dashboard/`)
  3. Image Prediction Page with drag-and-drop dropzone (`/predict/`)
  4. Prediction Result Page with probability breakdown (`/predictions/<id>/result/`)
  5. Prediction History with search, filter, and pagination (`/history/`)
  6. Prediction Detail with researcher observation notes editor (`/predictions/<id>/`)
  7. About SKYsense AI (`/about/`)
  8. Model Architecture & Specifications (`/model/`)
  9. Research & Evaluation Metrics with confusion matrix (`/metrics/`)
- Built REST API endpoint (`POST /api/predict/`).
- Added management command `seed_demo_data` to populate initial test records.
- Verified 100% passing tests in `predictions/tests.py`.
- Conducted visual tour verification via browser agent.

## Day 5

Goal: Production Database Layer & Django Admin Integration
Completed:
- Created formal `Prediction` model in `05_Backend/predictions/models.py`.
- Implemented all required fields: `id`, `image`, `original_filename`, `predicted_class`, `confidence`, `low_to_medium_probability`, `medium_to_heavy_probability`, `no_to_low_probability`, `created_at`, `processing_time`, `model_version`.
- Added optional edge IoT sensor fields: `source_type` (WEB_UPLOAD, IOT_DEVICE, API), `device_id`, `latitude`, `longitude`, `temperature`, `humidity`.
- Configured default ingestion channel to `WEB_UPLOAD` without fabricating IoT telemetry.
- Enforced database validation: probability sum integrity in `clean()`, value ranges `[0.0, 1.0]`, and coordinate pairing.
- Configured high-performance database indexes on `created_at`, `predicted_class`, `source_type`, `confidence`, `device_id`, and `model_version`.
- Engineered comprehensive Django Admin interface with specimen thumbnail previews, styled status badges, confidence meters, and fieldsets.
- Created clean initial migration (`0001_initial.py`) and applied to SQLite.
- Created admin superuser (`admin` / `admin1234`).
- Expanded automated test suite to 8 passing tests (`Ran 8 tests in 9.296s -> OK`).

## Day 6

Goal: Main Real-Time Meteorological Dashboard & Chart.js Integration
Completed:
- Implemented dynamic database-backed KPI cards: TOTAL ANALYSES, TODAY'S ANALYSES, AVERAGE CONFIDENCE, and MOST RECENT PREDICTION.
- Integrated 3 live Chart.js visualizations:
  1. Predictions by Rainfall Category (Doughnut Chart)
  2. Predictions Over Time (Activity Timeline Line/Area Chart)
  3. Confidence Distribution (5-bracket Histogram Bar Chart)
- Built interactive Recent Predictions table with image thumbnails, classification badges, confidence meters, UTC timestamps, and view links.
- Implemented graceful zero-state design when database contains 0 records without fake statistics.
- Added quick action: "Analyze New Image".
- Created REST API endpoint `GET /api/dashboard/stats/` returning live database telemetry.
- Validated all 11 unit and integration tests across `core` and `predictions` apps (`Ran 11 tests in 36.426s -> OK`).