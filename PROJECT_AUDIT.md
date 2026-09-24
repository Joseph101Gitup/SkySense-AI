# SKYsense AI - Comprehensive Project Audit & Architectural Assessment

**Project Title:** SKYsense AI - AI-Based Cloud-Image Rainfall Classification System  
**Lead Software Engineer:** AI Pair Programmer / System Architect  
**Project Location:** `D:\personal\SkySense_AI`  
**Remote Repository:** `https://github.com/Joseph101Gitup/SkySense-AI.git`  
**Audit Date:** 2026-09-23  
**Status:** Completed (Pre-Implementation Baseline Audit)

---

## 1. Executive Summary

This audit provides a rigorous, ground-truth evaluation of the **SKYsense AI** repository. SKYsense AI is designed as a cloud-image-based meteorological intelligence system for hyper-local rainfall classification.

At this stage:
- The core AI proof-of-concept exists exclusively inside Google Colab Jupyter notebooks using an **Xception** transfer learning backbone.
- The model classifies sky images into **3 rainfall categories** derived from an aggregated mapping of the **CCSN (Cirrus, Cumulus, Stratus, Nimbus) Database**.
- **Important Scientific Integrity Clarification:** The existing model predicts **3 rainfall intensity levels**, **NOT** an independently validated 11-class cloud-type classification. The model must not be falsely represented as a cloud-type classifier.
- No model weights (`.keras`, `.h5`, `.tflite`) or raw image datasets are currently committed or stored locally within the repository.
- The backend, API layers, and simulator modules (`04`, `05`, `06`, `07`, `08`, `09`, `10`) are currently empty skeleton directories.
- A critical label-indexing mismatch was discovered between the training generator and the inference/Gradio code in the original notebook, which inverted predictions during testing.

---

## 2. Current Architecture

```
+-----------------------------------------------------------------------------------+
|                            EXISTING SYSTEM WORKFLOW                               |
+-----------------------------------------------------------------------------------+
|  CCSN Dataset (KaggleHub: mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database)  |
|                                       |                                           |
|                                       v                                           |
|                   11 Meteorological Cloud Folders (CCSN_v2)                       |
|               [Ci, Cs, Cc, Ac, As, Sc, St, Ns, Cb, Cu, Ct]                        |
|                                       |                                           |
|                                       v                                           |
|       Rule-Based Re-aggregation into 3 Target Rainfall Classes                    |
|       - No_to_Low_Rain       <- Ci, Cs, Cc, Ac (915 images)                       |
|       - Low_to_Medium_Rain   <- As, Sc, St, Ns (1,004 images)                     |
|       - Medium_to_Heavy_Rain <- Cb, Cu, Ct     (624 images)                       |
|                                       |                                           |
|                                       v                                           |
|             Keras ImageDataGenerator (rescale 1/255, 256x256, B=32)               |
|            (Validation split 0.20 inherits training augmentation)                 |
|                                       |                                           |
|                                       v                                           |
|                     Two-Phase Transfer Learning (Xception)                        |
|                     Phase 1: Frozen backbone (30/50 epochs)                       |
|                     Phase 2: Fine-tuning @ lr=1e-5 (30/50 epochs)                 |
|                                       |                                           |
|                                       v                                           |
|                          Ad-hoc Inference Endpoints                               |
|        +------------------------------+------------------------------+            |
|        |                              |                              |            |
|        v                              v                              v            |
| predict_local_weather()         Gradio Web App               OpenCV Webcam        |
| (Index bug: misaligned)       (Index bug: misaligned)     (Broken model path/GUI) |
+-----------------------------------------------------------------------------------+
```

---

## 3. Current AI Pipeline Inspection

### 3.1 Model Architecture
- **Backbone:** Xception (pre-trained on ImageNet, top classification head removed).
- **Input Dimensions:** `(256, 256, 3)` RGB.
- **Preprocessing:** Pixel rescale factor $1/255.0$ (normalized to $[0.0, 1.0]$).
- **Classification Head:**
  - `GlobalAveragePooling2D()` (reduces 2048 feature maps to a 2048-dimensional vector).
  - `Dropout(rate=0.4)` (regularization).
  - `Dense(3, activation='softmax')` (probability distribution over 3 rainfall classes).
- **Parameter Distribution:**
  - Total Parameters: **20,867,627** (~79.60 MB).
  - Trainable Parameters (Phase 1): **6,147** (~24.01 KB).
  - Non-Trainable Parameters (Phase 1): **20,861,480** (~79.58 MB).
  - Trainable Parameters (Phase 2): **20,813,107** (~79.39 MB).

### 3.2 Training Strategy & Hyperparameters
1. **Phase 1 (Feature Extraction):**
   - Backbone frozen (`base_model.trainable = False`).
   - Optimizer: `Adam(learning_rate=default (0.001))`.
   - Loss Function: `categorical_crossentropy`.
   - Batch Size: `32`.
   - Result: ~67.5% - 70.38% training accuracy, ~54.6% - 55.82% validation accuracy.
2. **Phase 2 (Fine-Tuning):**
   - Backbone unfrozen (`base_model.trainable = True`).
   - Optimizer: `Adam(learning_rate=1e-5)`.
   - Result: ~91.06% - 96.41% training accuracy, ~60.36% - 62.13% validation accuracy.
   - **Severe Generalization Gap:** The ~30-35% delta between training accuracy and validation accuracy signals severe overfitting and data pipeline shortcomings.

### 3.3 Prediction & Application Logic
- **Single Image Prediction (`predict_local_weather`):** Loads image with target size $256 \times 256$, expands batch dimension, applies $/255.0$, and predicts. Uses hardcoded class names `["No Rain to Very Low Rain", "Low to Medium Rain", "Medium to Heavy/High Rain"]`.
- **Gradio Interface:** Interactive upload tool with probability bars. Uses hardcoded class names `['No_to_Low_Rain', 'Low_to_Medium_Rain', 'Medium_to_Heavy_Rain']`.
- **OpenCV Webcam Feed:** Loops over `cv2.VideoCapture(0)`, flips frame, renders bounding boxes and probability bars. Hardcoded to load `'cloud_rain_model.h5'` (which was not saved prior to this cell).

---

## 4. Verified Dataset Information

The system utilizes the **CCSN (Cirrus, Cumulus, Stratus, Nimbus) Database** downloaded via KaggleHub (`mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database`).

### 4.1 Ground-Truth Class Breakdown
| Class Index | Verified Class Name | Source Meteorological Cloud Types Included | Image Count | Percentage |
| :---: | :--- | :--- | :---: | :---: |
| **0** | **`Low_to_Medium_Rain`** | Altostratus (`As`), Stratocumulus (`Sc`), Stratus (`St`), Nimbostratus (`Ns`) | **1,004** | 39.48% |
| **1** | **`Medium_to_Heavy_Rain`** | Cumulonimbus (`Cb`), Cumulus (`Cu`), Cirrostratus/Altocumulus thick (`Ct`) | **624** | 24.54% |
| **2** | **`No_to_Low_Rain`** | Cirrus (`Ci`), Cirrostratus (`Cs`), Cirrocumulus (`Cc`), Altocumulus (`Ac`) | **915** | 35.98% |
| **Total** | | | **2,543** | **100.00%** |

### 4.2 Verified Input Specifications
- **Dimensions:** $256 \times 256 \times 3$ (Height, Width, Channels: RGB).
- **Pixel Normalization:** $0.0 \text{ to } 1.0$ ($x / 255.0$).
- **Batch Size:** $32$.
- **Color Format:** RGB.

---

## 5. Verified Class Mapping & The Critical Inversion Bug

### 5.1 Keras Directory Order Ground Truth
When `ImageDataGenerator.flow_from_directory(base_target_dir, ...)` parses subfolders, it sorts class names **alphabetically**:
1. `Low_to_Medium_Rain` $\rightarrow$ **Index 0**
2. `Medium_to_Heavy_Rain` $\rightarrow$ **Index 1**
3. `No_to_Low_Rain` $\rightarrow$ **Index 2**

### 5.2 The Existing Flaw in Inference Code
In both notebook versions, the inference code defines labels manually in a different order:
- **Notebook Cell 6 (`predict_local_weather`):**
  ```python
  classes = ["No Rain to Very Low Rain", "Low to Medium Rain", "Medium to Heavy/High Rain"]
  # Index 0 was wrongly interpreted as No Rain!
  # Index 1 was correctly Low to Medium Rain.
  # Index 2 was wrongly interpreted as Medium to Heavy Rain!
  ```
- **Notebook Cell 10 (Gradio):**
  ```python
  class_names = ['No_to_Low_Rain', 'Low_to_Medium_Rain', 'Medium_to_Heavy_Rain']
  # Index 0 was wrongly assigned to No_to_Low_Rain!
  # Index 1 was wrongly assigned to Low_to_Medium_Rain!
  # Index 2 was wrongly assigned to Medium_to_Heavy_Rain!
  ```
- **Consequence:** Predictions evaluated through Gradio and `predict_local_weather()` presented inverted meteorological assessments: clear skies with thin cirrus clouds (Index 2) were output as "Medium to Heavy Rain", and low rain clouds (Index 0) were output as "No Rain".
- **Resolution:** All future pipelines must strictly bind classes programmatically using `train_generator.class_indices` and export a canonical `class_mapping.json` configuration file.

---

## 6. Current Model Limitations

1. **Absence of Independent Test Split:**
   - The dataset was split 80% training / 20% validation.
   - Validation was evaluated during hyperparameter tuning and epoch selection. No held-out test set exists to provide an unbiased generalization benchmark.
2. **Data Leakage in Validation Preprocessing:**
   - The validation generator in the notebook inherited the data augmentation parameters (random rotation, shifts, and horizontal flips) from the training generator.
   - Validation metrics must be measured strictly on clean, unaugmented, deterministic images.
3. **Severe Overfitting:**
   - Training accuracy reached 91%–96%, while validation accuracy plateaued at 60%–62%.
   - Indicates memorization of specific image artifacts rather than meteorological features.
4. **Class Imbalance:**
   - `Medium_to_Heavy_Rain` has only 624 samples compared to 1,004 samples for `Low_to_Medium_Rain`. No class weighting or focal loss was applied.
5. **No Cloud-Type Classification:**
   - The system collapses 11 meteorological cloud types into 3 rainfall categories. It cannot output cloud type predictions.
6. **No Explainability (XAI):**
   - The system lacks visual attribution (such as Grad-CAM heatmaps) to verify whether the CNN is focusing on cloud bodies or edge noise (trees, buildings, ground artifacts).
7. **No Local Model Artifacts on Disk:**
   - Model weights were saved inside transient Google Colab containers and were not persisted to `03_AI_Model/saved_models/`.

---

## 7. Current Environment & Dependency Realities

### 7.1 Local Machine Environment Audit
- **Operating System:** Windows 10/11
- **Python Version:** `3.14.2`
- **Git Version:** `2.52.0.windows.1`
- **Java Version:** `25.0.2 LTS`
- **Web Framework Installed:** `Django 6.0.1`, `djangorestframework 3.17.1`

### 7.2 Critical Environmental Risk: Python 3.14 vs Deep Learning Libraries
- **TensorFlow:** As of Q1 2026, official TensorFlow binary wheels support Python 3.9 through Python 3.12 (with experimental builds on 3.13). **There are no stable TensorFlow precompiled wheels for Python 3.14 on Windows.**
- **Existing `.venv` Status:** The virtual environment at `03_AI_Model/.venv` fails with `uv trampoline failed to canonicalize script path` when executing `pip.exe`.
- **Architectural Solution:**
  1. The Django web backend, APIs, database, and front-end interface run cleanly on the current Python 3.14.2 host.
  2. For the AI Inference Pipeline:
     - Export trained models to **ONNX** or **TensorFlow Lite (TFLite)** format, allowing lightweight runtime inference decoupled from full TensorFlow training builds.
     - Alternatively, maintain training scripts for execution in Google Colab (GPU) or a dedicated Python 3.11/3.12 environment, exporting `.onnx` / `.tflite` / `.keras` weights for deployment into the Django service.

---

## 8. What Works, What Is Incomplete, What Must Be Preserved & Created

### 8.1 What Already Works
- **Concept & Baseline Feasibility:** Proved that transfer learning from ImageNet-pretrained Xception can learn features from the CCSN dataset.
- **Rule-Based Mapping:** Validated mapping logic from 11 CCSN classes to 3 rainfall potential categories.
- **Project Structure Blueprint:** Clear 16-module directory taxonomy in repository.
- **Git & GitHub Integration:** Connected to remote repository `Joseph101Gitup/SkySense-AI.git`.
- **Project Planning Documentation:** Comprehensive baseline analysis and milestone schedules in `01_Project_Management` and `02_Research`.

### 8.2 What Is Incomplete
- **Trained Model Artifacts:** No `.keras`, `.onnx`, or `.tflite` model files exist on disk.
- **Local Dataset:** Dataset directories `08_Dataset` and `03_AI_Model/datasets` are empty.
- **Backend Architecture:** `05_Backend` has no Django project files, models, views, or endpoints.
- **Inference Service:** No production Python inference module exists outside the Colab notebook.
- **Evaluation Artifacts:** No confusion matrix metrics, ROC curves, or classification reports (`precision`, `recall`, `f1-score`) generated for an independent test set.

### 8.3 What Should Be Preserved
- `03_AI_Model/Cloud_recognishion_and_rain_prediction.ipynb` (original baseline proof of concept).
- `03_AI_Model/notebooks/Cloud_Recognition_Day2_5_Verification.ipynb.ipynb` (extended verification notebook).
- All research notes and baseline documentation in `02_Research/`.
- Project management timelines and milestones in `01_Project_Management/`.

### 8.4 What Should Be Refactored
- **Label Mapping:** Programmatically enforce alphabetical class index matching across all scripts and serialization schemas.
- **Inference Logic:** Extract inference routines from notebooks into modular, standalone Python classes (`inference_engine.py`).
- **Validation Pipeline:** Decouple validation and test data generators from training data augmentations.
- **Virtual Environment:** Re-establish a clean virtual environment for Python development.

### 8.5 What Needs To Be Created
1. **Canonical Config:** `config.py` and `class_mapping.json` defining model parameters and class indices.
2. **Modular AI Pipeline Scripts:**
   - `dataset_downloader.py`: Automated reproducible download and sorting of the CCSN dataset into 3 classes.
   - `data_loader.py`: Stratified Train / Validation / Test split (e.g. 70% / 15% / 15%) with augmentation applied *only* to training.
   - `model_factory.py`: Modular model architecture definition (Xception backbone + custom head).
   - `train.py`: Reproducible training script with EarlyStopping, ModelCheckpoint, and TensorBoard logging.
   - `evaluate.py`: Generation of precision, recall, F1-score, and confusion matrix on the independent test set.
   - `export_model.py`: Model conversion to ONNX and TFLite for production backend deployment.
3. **Django Web Application (`05_Backend`):**
   - Django project (`skysense_core`) with app (`rainfall_predictor`).
   - REST API endpoints for image upload and rainfall prediction.
   - Web interface for drag-and-drop cloud image analysis, displaying rainfall probability, meteorological context, and advisory warnings.
   - Prediction history tracking with SQLite/PostgreSQL storage.

---

## 9. Proposed Final Architecture (Production & Academic Master's Standard)

```
+-----------------------------------------------------------------------------------+
|                        PROPOSED SKYSENSE AI ARCHITECTURE                          |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Presentation Layer / Web UI ]                                                  |
|  - Modern, responsive Dashboard (HTML5 / Vanilla CSS / Glassmorphism Design)      |
|  - Cloud Image Drag-and-Drop & File Upload                                        |
|  - Real-Time Prediction Visualizer (Gauge / Confidence Bars)                      |
|  - Meteorological Advisory & Action Recommendations                               |
|  - Prediction History & Audit Trail                                               |
|                                                                                   |
|                                       | HTTP POST / Multi-part                     |
|                                       v                                           |
|  [ Django Web & API Core (05_Backend) ]                                           |
|  - Django 6.0 REST API (POST /api/v1/predict/, GET /api/v1/history/)              |
|  - Input Validation & Image Security Sanitizer (Pillow: 256x256 RGB check)        |
|  - Image Storage & Metadata Registry (SQLite / Database)                          |
|                                                                                   |
|                                       | Internal Call                             |
|                                       v                                           |
|  [ AI Inference Engine Service (03_AI_Model / 05_Backend/services) ]              |
|  - Preprocessing Service: Deterministic 256x256 Rescaling (0.0 to 1.0)            |
|  - Model Runtime (ONNX Runtime / TFLite / Keras)                                  |
|  - Softmax Probability Vector Generation                                          |
|  - Canonical Label Mapping Verification (Indices 0, 1, 2)                         |
|  - Meteorological Context & Confidence Engine                                     |
|                                                                                   |
|                                       | Logs & Metrics                            |
|                                       v                                           |
|  [ Evaluation, Explainability & Artifacts ]                                       |
|  - Independent 3-Way Split (Train / Val / Test)                                   |
|  - Metrics: Confusion Matrix, Macro/Weighted F1, Precision, Recall                |
|  - Explainability: Grad-CAM Heatmap Generation (Future Enhancement)               |
+-----------------------------------------------------------------------------------+
```

---

## 10. Implementation Roadmap

### Phase 1: AI Pipeline Stabilization & Modularization
- Create canonical configuration (`class_mapping.json`, `config.yaml`).
- Create modular dataset preparation script (download, class aggregation, train/val/test split).
- Fix label indexing bug and enforce alphabetical binding.
- Create evaluation suite yielding classification report and confusion matrix.
- Export trained model weights to production-ready formats (`.keras`, `.onnx`/`.tflite`).

### Phase 2: Django Backend & API Architecture
- Initialize Django project inside `05_Backend`.
- Build `rainfall_predictor` app with REST endpoints.
- Integrate the AI Inference Service with pre-allocated models.
- Implement database models for storing predictions, confidence scores, and timestamps.
- Build automated unit tests for API and inference logic.

### Phase 3: Premium Frontend User Experience
- Build responsive, modern web UI adhering to design best practices (clean typography, glassmorphism, responsive layout).
- Connect UI to backend APIs for live image upload, prediction display, and historical logging.

### Phase 4: Verification, Benchmarking & Master's Project Documentation
- Run complete end-to-end integration tests.
- Compile experimental evaluation results into `02_Research` and `10_Documentation`.
- Ensure strict academic integrity regarding model capabilities (clarifying rainfall classification vs cloud typing).

---

## 11. Risk Register & Mitigation Strategy

| Risk ID | Description | Severity | Likelihood | Mitigation Strategy |
| :---: | :--- | :---: | :---: | :--- |
| **RISK-01** | Python 3.14 incompatibility with TensorFlow wheels on Windows | High | High | Decouple training and runtime. Use ONNX / TFLite runtime in the Django application; execute heavy training in Colab or Python 3.11 virtual environment. |
| **RISK-02** | Overfitting and low validation accuracy (~61%) | High | High | Implement independent test set, remove validation augmentation, explore data augmentation tuning, test class weights, and evaluate transfer models (EfficientNetB0/ConvNeXt). |
| **RISK-03** | Label indexing bug recurrence | Critical | Low | Enforce single source of truth (`class_mapping.json`) verified by unit tests before every inference call. |
| **RISK-04** | Missing local model artifacts | Medium | High | Download and verify baseline `.keras` weights from Colab or produce reproducible local export script. |
| **RISK-05** | Academic misrepresentation of cloud classification | High | Low | Explicitly document in all reports and UI that the model classifies **rainfall intensity levels**, not discrete cloud genera. |

---

## 12. Dependencies Matrix

### Runtime Dependencies (Web & Inference)
- `Python >= 3.11` (Current system: `3.14.2`)
- `Django >= 5.1` (Current system: `6.0.1`)
- `djangorestframework >= 3.15` (Current system: `3.17.1`)
- `numpy >= 1.26` (Current system: `2.5.1`)
- `pillow >= 10.0` (Current system: `12.1.1`)
- `onnxruntime` or `tflite-runtime` (for portable inference)

### Training & Research Dependencies (Colab / Dedicated Training Env)
- `tensorflow >= 2.15` (Recommended Python 3.10-3.12)
- `kagglehub`
- `scikit-learn` (for confusion matrices, classification reports)
- `matplotlib`, `seaborn` (for evaluation visualizations)
