# SKYsense AI: Deep Learning Model Specification & Empirical Evaluation

**Document Version**: 2.0  
**Model Identifier**: `Xception-v1.0 (Deep Transfer CNN)`  
**Target Domain**: Computer Vision Meteorological Cloud-to-Rainfall Inference  
**Evaluation Partition**: Independent Held-Out Test Split ($N = 381$)

---

## 1. Dataset & Meteorological Categorization

The AI model is trained on ground-based sky photography derived from the **CCSN (Cirrus Cumulus Stratus Nimbus) Database**:

- **Total Sample Scale**: 2,543 verified photographic specimens.
- **Source Resolution**: Native ground-camera photographs (ranging from $400 \times 400$ to high-definition photographic frames).
- **Physical Classification**: In accordance with World Meteorological Organization (WMO) cloud classification standards, the 11 constituent cloud genera are mapped into 3 actionable precipitation regimes based on cloud water content, optical thickness, and precipitation physics:

| Aggregated Precipitation Regime | Included Cloud Genera | Meteorological & Physical Characteristics |
|---|---|---|
| **`No_to_Low_Rain`** (Class 2) | Cirrus (`Ci`), Cirrostratus (`Cs`), Cirrocumulus (`Cc`), Altocumulus (`Ac`), Contrails (`Ct`) | High-altitude ice-crystal clouds (above 6,000 m) or shallow mid-level altocumulus. Characterized by negligible liquid water content and zero ground precipitation probability. |
| **`Low_to_Medium_Rain`** (Class 0) | Altostratus (`As`), Stratus (`St`), Stratocumulus (`Sc`), Nimbostratus (`Ns`) | Stratiform, horizontally layered cloud decks. Characterized by stable atmospheric conditions, moderate liquid water content, generating light drizzle to steady moderate rainfall. |
| **`Medium_to_Heavy_Rain`** (Class 1) | Cumulonimbus (`Cb`), Cumulus (`Cu`) | Deep convective cloud towers with intense vertical updrafts and downdrafts. Characterized by massive ice/water mass, supercooled droplets, heavy downpours, lightning, and severe convective precipitation. |

---

## 2. Image Preprocessing & Data Pipeline

Every image passes through a deterministic tensor preprocessing pipeline prior to convolutional feature extraction:

1. **Decoding & Verification**: Raw byte streams are verified with Pillow (`Image.open()`), discarding truncated or corrupt files.
2. **Spatial Resampling**: Bilinear interpolation rescales input imagery to $256 \times 256 \times 3$ (Height $\times$ Width $\times$ RGB Channels).
3. **Tensor Normalization**: Pixel intensity values are scaled linearly from $[0, 255]$ into floating-point range $[0.0, 1.0]$ via $x_{\text{norm}} = \frac{x}{255.0}$.
4. **Data Augmentation (Training Phase Only)**:
   - Random horizontal flipping (`horizontal_flip = True`)
   - Random rotation ($\pm 15^\circ$)
   - Random width and height shifts ($\pm 10\%$)
   - Random zoom ($\pm 10\%$)
   - Brightness jitter ($[0.9, 1.1]$)
   *Note: Validation and Test splits are never augmented to preserve pure out-of-sample benchmark validity.*

---

## 3. Stratified Data Partitioning (Zero Data Leakage)

The 2,543 specimens were partitioned using deterministic stratified sampling to ensure identical class distributions across all subsets:

```text
Total Dataset (2,543 Specimens)
 ├── Train Split (70%):       1,779 specimens (Used for parameter optimization)
 ├── Validation Split (15%):    383 specimens (Used for hyperparameter tuning & early stopping)
 └── Test Split (15%):          381 specimens (Strictly held-out; used only for final evaluation)
```

- **Partition Integrity**: Every image file resides strictly in one partition; hashes and filenames verify zero overlap.
- **Stratification Proportions**:
  - `Low_to_Medium_Rain`: ~39.4%
  - `Medium_to_Heavy_Rain`: ~24.4%
  - `No_to_Low_Rain`: ~36.2%

---

## 4. Deep Learning Backbone: Xception Architecture

The core feature extraction engine utilizes **Xception** (Extreme Inception), a 71-layer deep convolutional neural network proposed by François Chollet:

```text
[Input Tensor: 256x256x3]
         │
         ▼
[Entry Flow]
  ├── Standard Conv2D (32 filters, 3x3, stride 2) + ReLU
  ├── Standard Conv2D (64 filters, 3x3) + ReLU
  └── 3x Residual Depthwise Separable Conv Blocks with Max Pooling (stride 2)
         │
         ▼
[Middle Flow]
  └── 8x Repeated Residual Blocks
      └── 3x Depthwise Separable Conv2D (728 filters, 3x3) + ReLU + Identity Skip Connection
         │
         ▼
[Exit Flow]
  ├── 1x Residual Depthwise Separable Conv Block (728 to 1024 filters) + Max Pooling
  └── 2x Depthwise Separable Conv2D (1536 & 2048 filters, 3x3) + ReLU
         │
         ▼
[Global Average Pooling 2D] ──► (2048-dimensional feature vector)
         │
         ▼
[Dropout Layer (rate = 0.30)] ──► Regularization
         │
         ▼
[Dense Output Layer (3 units, Softmax)] ──► Categorical Probabilities
```

### Why Depthwise Separable Convolutions?
Standard convolutions look at channel correlations and spatial correlations simultaneously. Xception separates them:
1. **Depthwise Convolution**: Applies a spatial $3 \times 3$ filter independently to each input channel.
2. **Pointwise Convolution**: Applies a $1 \times 1$ convolution across all channels to project channels into a new feature space.

This decouples cross-channel correlations from spatial correlations, dramatically reducing computational complexity ($O(D_K^2 \cdot M \cdot N)$ vs. $O(D_K^2 \cdot M + M \cdot N)$) while outperforming traditional architectures (VGG16, ResNet50) on complex natural cloud textures.

---

## 5. Transfer Learning & Two-Phase Fine-Tuning

Training an architecture of this scale (20.8M parameters) from scratch on 2,543 cloud images would cause severe overfitting. A two-phase transfer learning methodology was implemented:

### Phase 1: Feature Extraction
- **Weights Initialization**: Pre-trained on ImageNet ($1.4 \times 10^6$ natural images, 1,000 classes).
- **Backbone State**: All 132 convolutional layers frozen (`base_model.trainable = False`).
- **Trainable Parameters**: Only the custom top head ($2048 \times 3 + 3 = 6,147$ parameters).
- **Optimizer**: Adam ($\text{learning\_rate} = 1 \times 10^{-3}$).
- **Loss Function**: Categorical Cross-Entropy:
  $$\mathcal{L} = -\sum_{i=1}^{C} y_i \log(\hat{y}_i)$$
- **Epochs**: 10 epochs.

### Phase 2: Fine-Tuning
- **Unfreezing**: The top 30 convolutional layers of Xception unfrozen; bottom layers remain frozen to preserve low-level edge and texture detectors.
- **Trainable Parameters**: ~4.8 million parameters.
- **Optimizer**: Adam with conservative learning rate ($\text{learning\_rate} = 1 \times 10^{-5}$).
- **Regularization**:
  - `Dropout(0.30)` before the dense classification layer.
  - `EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)`.
  - `ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-7)`.
- **Checkpointing**: Model checkpointing on validation loss to `models/best_xception_rainfall.keras`.

---

## 6. Empirical Performance Metrics (Independent Test Split)

Evaluation conducted on the strictly held-out test partition ($N = 381$ specimens):

| Evaluation Metric | Benchmark Value | Description |
|---|:---:|---|
| **Overall Test Accuracy** | **58.27%** | Exact multiclass top-1 classification accuracy on unseen test data. |
| **Test Categorical Loss** | **0.9103** | Mean categorical cross-entropy loss. |
| **Macro Average Precision** | **61.23%** | Unweighted average precision across all 3 classes. |
| **Macro Average Recall** | **55.74%** | Unweighted average recall across all 3 classes. |
| **Macro Average F1-Score** | **56.60%** | Harmonic mean of macro precision and macro recall. |
| **Weighted Average F1-Score** | **57.58%** | Support-weighted average F1-score across all 3 classes. |

### Per-Class Performance Breakdown

| Class Name | Precision | Recall | F1-Score | Support ($N$) |
|---|:---:|:---:|:---:|:---:|
| **`Low_to_Medium_Rain`** | 0.5400 (54.0%) | 0.7200 (72.0%) | 0.6171 (61.7%) | 150 |
| **`Medium_to_Heavy_Rain`** | 0.6923 (69.2%) | 0.3871 (38.7%) | 0.4966 (49.7%) | 93 |
| **`No_to_Low_Rain`** | 0.6047 (60.5%) | 0.5652 (56.5%) | 0.5843 (58.4%) | 138 |
| **Total / Summary** | **0.6123** | **0.5574** | **0.5758** | **381** |

---

## 7. Confusion Matrix Analysis

The confusion matrix on the 381 unseen test specimens exhibits the following numerical distribution:

```text
                         PREDICTED CLASS
                    Low_to_Med   Med_to_Heavy   No_to_Low   Total
ACTUAL  Low_to_Med       108          10           32        150
CLASS   Med_to_Heavy      38          36           19         93
        No_to_Low         54           6           78        138
        Total            200          52          129        381
```

### Scientific Interpretations:
1. **Strong Stratiform Detection (Recall = 72.0%)**:
   The model excels at identifying stratiform cloud decks (`Low_to_Medium_Rain`), correctly classifying 108 out of 150 test specimens. Stratiform features (uniform grey overcast, diffuse illumination) provide clear spatial signals.
2. **Convective Specificity vs. Sensitivity (Precision = 69.2%, Recall = 38.7%)**:
   When the model predicts `Medium_to_Heavy_Rain`, it is reliable 69.2% of the time (high precision, low false alarm rate). However, 38 convective specimens were classified as `Low_to_Medium_Rain` because distant towering cumulus or developing cumulonimbus often share visual boundary textures with dense stratocumulus clouds.
3. **Clear Weather Separation**:
   Only 6 non-rainy cloud specimens (`No_to_Low_Rain`) were falsely predicted as `Medium_to_Heavy_Rain` (1.5% false heavy alarm rate), confirming strong discrimination between cirrus/altocumulus and severe convective storm cells.

---

## 8. Real-Time Inference Performance

- **Model Serialization**: `models/best_xception_rainfall.keras` (HDF5/Keras zip format, ~245 MB).
- **Exported Edge Model**: `models/best_xception_rainfall.tflite` (Quantized/Float32 flatbuffer, ~20.5 MB).
- **Latency Benchmarks**:
  - Intel Core i7 / AMD Ryzen CPU: **35 ms – 70 ms** per 256×256 frame.
  - Raspberry Pi 4 Model B (TFLite runtime): **180 ms – 320 ms** per frame.

---

## 9. Scientific & Technical Limitations

1. **2D Optical Field-of-View**: Ground-level cameras capture only the cloud base from below. They cannot measure vertical cloud thickness, cloud top height, or radar reflectivity (dBZ), which are critical for precision rainfall rate quantification.
2. **Absence of Temporal Dimension**: Single-frame classification lacks temporal velocity. A developing storm cell and a decaying cumulonimbus look similar optically in a single snapshot.
3. **Sunlight & Sun Angle Variations**: Dawn/dusk lighting and direct sun glare can artificially skew normalized RGB channel histograms.
4. **Precipitation vs. Cloud Type Decoupling**: While nimbostratus and cumulonimbus indicate high rain likelihood, local terrain and dry sub-cloud air layers can cause virga (rain that evaporates before reaching ground sensors).
