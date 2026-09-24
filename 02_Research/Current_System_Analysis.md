# Current System Analysis

## Project Name
Cloud Recognition and Rain Prediction

## Objective
Classify cloud images and predict rainfall intensity.

## Dataset
CCSN Dataset

## Framework
TensorFlow / Keras

## Model
Xception (Transfer Learning)

## Input Size
256 x 256

## Output Classes
- No_to_Low_Rain
- Low_to_Medium_Rain
- Medium_to_Heavy_Rain

## Strengths
(To be completed)

## Weaknesses
(To be completed)

## Future Improvements
(To be completed)




1. Existing Project Title

The notebook filename is:

Cloud_recognishion_and_rain_prediction (1).ipynb

The implemented system is essentially a:

Cloud Image-Based Rainfall Prediction System using Xception Transfer Learning

The current notebook predicts rainfall categories from cloud images. It does not yet perform actual IoT sensor-based prediction, and it does not currently classify the original 11 cloud types as its final output. The original cloud categories are grouped into three rainfall categories.

2. Objective of the Existing System

The implemented system takes an image of the sky/clouds and uses a deep-learning image-classification model to predict one of three rainfall-intensity categories:

No to Low Rain
Low to Medium Rain
Medium to Heavy Rain

The model is subsequently used for individual image prediction, a Gradio web interface, and an OpenCV webcam-based interface.

3. Development Environment Used

The notebook was executed in Google Colab.

The notebook metadata specifies:

Item	Value
Platform	Google Colab
Programming language	Python
Kernel	Python 3
Accelerator	GPU
GPU	NVIDIA T4
Deep Learning framework	TensorFlow / Keras
Dataset download library	KaggleHub
Image processing	OpenCV
Visualization	Matplotlib
Web interface	Gradio

The notebook metadata explicitly records a T4 GPU accelerator.

4. Dataset
Dataset Used

The notebook downloads:

Cirrus, Cumulus, Stratus, Nimbus (CCSN) Database

using KaggleHub.

The dataset identifier used in the notebook is:

mmichelli/cirrus-cumulus-stratus-nimbus-ccsn-database

The downloaded archive size recorded by the notebook was approximately:

93.2 MB

The extracted dataset directory was:

CCSN_v2

The notebook successfully located the cloud-class directories and processed the dataset.

5. Original Cloud Categories

The notebook searches for cloud folders including:

Ci
Cs
Cc
Ac
As
Sc
St
Ns
Cb
Cu
Ct

These are then grouped into three rainfall-related categories.

Mapping Used
Rainfall Category	Original Cloud Classes
No_to_Low_Rain	Ci, Cs, Cc, Ac
Low_to_Medium_Rain	As, Sc, St, Ns
Medium_to_Heavy_Rain	Cb, Cu, Ct

This mapping is explicitly implemented in the notebook.

6. Dataset Size

The notebook reports:

2,543 images successfully sorted into 3 rainfall categories.

The dataset is divided using an 80/20 validation split.

Training

2,036 images

Validation

507 images

Total

2,543 images

The notebook output explicitly reports 2,036 training images and 507 validation images.

Report Table
Dataset	Images	Percentage
Training	2,036	80%
Validation	507	20%
Total	2,543	100%

Important: the notebook does not provide the number of images belonging to each of the three rainfall classes. Do not put class-wise counts into your report unless we calculate them later.

7. Image Preprocessing

The notebook uses TensorFlow/Keras ImageDataGenerator.

Pixel Normalization
rescale = 1./255

This converts pixel values to the range approximately:

0–255 → 0–1
Image Size
256 × 256 pixels
Batch Size
32
Classification Mode
categorical

Therefore the model uses categorical classification with three output classes.

8. Data Augmentation

The training generator applies:

Augmentation	Value
Rotation	±25°
Width shift	0.2
Height shift	0.2
Horizontal flip	Enabled
Rescaling	1/255
Validation split	20%

The augmentation configuration is explicitly present in the notebook.

Report Description

You can write:

To improve the generalization capability of the model and reduce overfitting, image augmentation was applied during training. The augmentation pipeline included random rotations up to 25 degrees, horizontal and vertical shifts of 20%, horizontal flipping, and pixel normalization using a scaling factor of 1/255.

9. Deep Learning Model

The notebook uses:

Xception

with:

weights='imagenet'
include_top=False

Therefore, the system uses transfer learning from an Xception model pretrained on ImageNet.

The input shape is:

256 × 256 × 3

The original Xception classification head is removed and replaced with a custom classification head.

10. Model Architecture

The architecture is:

Input Image
256 × 256 × 3
       ↓
Xception Backbone
ImageNet Pretrained
       ↓
Global Average Pooling 2D
       ↓
Dropout
0.4
       ↓
Dense Layer
3 neurons
       ↓
Softmax
       ↓
Rainfall Class

The custom layers are:

GlobalAveragePooling2D()
Dropout(0.4)
Dense(3, activation='softmax')

The model is compiled with:

Optimizer: Adam
Loss: categorical_crossentropy
Metric: accuracy

11. Model Parameters

The notebook's model summary reports:

Parameter	Value
Total parameters	20,867,627
Trainable parameters during initial phase	6,147
Non-trainable parameters during initial phase	20,861,480
Approx. total parameter size	79.60 MB
Approx. trainable parameter size	24.01 KB
Approx. non-trainable parameter size	79.58 MB

This is useful for the AI Model Architecture section of your report.

12. Training Strategy

The notebook uses two-stage transfer learning.

Phase 1 — Feature Extraction

The Xception base model is frozen:

base_model.trainable = False

Only the new classification layer is trained.

Configuration
Parameter	Value
Epochs	30
Optimizer	Adam
Learning rate	Default Adam learning rate
Loss	Categorical Crossentropy
Metric	Accuracy
Batch size	32

13. Phase 1 Results

After 30 epochs:

Training
Accuracy = 70.38%
Loss = 0.7238
Validation
Accuracy = 55.82%
Loss = 0.9479

Phase 1 Summary
Metric	Result
Training Accuracy	70.38%
Training Loss	0.7238
Validation Accuracy	55.82%
Validation Loss	0.9479
14. Phase 2 — Fine-Tuning

In the second phase, the entire Xception base model is unfrozen:

base_model.trainable = True

The model is recompiled with:

Optimizer: Adam
Learning rate: 0.00001
Loss: categorical_crossentropy
Metric: accuracy

Training was performed for another:

30 epochs

15. Phase 2 Final Results

At Epoch 30:

Training
Accuracy = 91.06%
Loss = 0.2578
Validation
Accuracy = 61.74%
Loss = 1.1439

Phase 2 Summary
Metric	Result
Training Accuracy	91.06%
Training Loss	0.2578
Validation Accuracy	61.74%
Validation Loss	1.1439
16. Best Validation Accuracy Observed

During Phase 2, the highest validation accuracy recorded in the training log was:

62.13%

This occurred at:

Epoch 18

The final epoch's validation accuracy was lower at 61.74%.

This distinction is important.

For the report, don't simply say:

"The model achieved 91.06% accuracy."

That is training accuracy, not validation accuracy.

A technically accurate statement is:

"Following fine-tuning, the model achieved a training accuracy of 91.06%, while the highest validation accuracy observed during the recorded training run was 62.13%."

17. Training Time

The notebook provides epoch execution times.

For example, during Phase 2, epochs generally required approximately:

60–62 seconds per epoch

The first epoch required approximately:

260 seconds

The notebook does not provide a single total training time value, so we should not invent one.

18. Model Saving

The model was saved in two formats.

HDF5
xception_rainfall_model.h5
Native Keras
xception_rainfall_model.keras

The .keras file was downloaded from Google Colab, with the notebook recording a file size of approximately:

83,971,352 bytes

or roughly 84 MB.

The notebook also records a warning that HDF5 is considered a legacy format and recommends the native .keras format.

For the final project, we'll use:

.keras

as the primary training-model format.

19. Individual Image Prediction

The notebook contains a prediction function named:

predict_local_weather()

The process is:

Input Image
     ↓
Resize to 256 × 256
     ↓
Convert to Array
     ↓
Normalize /255
     ↓
Add Batch Dimension
     ↓
Xception Model
     ↓
Softmax Probabilities
     ↓
Predicted Rainfall Category

20. Example Prediction

The notebook tested an image:

plastic-06.jpg

The recorded output was:

Predicted Status : Low to Medium Rain
Confidence Level : 50.39%

It additionally produced:

Rain Probability : 40% - 75%

and the associated advisory text indicated drizzle or steady moderate rain.

⚠️ Important

Do not use this 50.39% prediction as a final model-performance result.

It is a single demonstration prediction, not an accuracy evaluation.

21. Gradio Interface

The notebook also implements a Gradio-based web interface.

The interface is titled:

Cloud Analysis & Rainfall Predictor

It allows the user to:

Upload a cloud image.
Click Analyze Sky.
Receive probability values for the three rainfall classes.

The interface uses:

Gradio
TensorFlow/Keras
NumPy
PIL

22. Gradio Interface Flow
User
  ↓
Upload Cloud Image
  ↓
Resize 256×256
  ↓
Normalize
  ↓
Xception Model
  ↓
Softmax Prediction
  ↓
Three Rainfall Probabilities

The notebook successfully launched the Gradio interface using a temporary public share link.

The link itself should not be included in the permanent report because it was a temporary Gradio share link.

23. Webcam Implementation

The notebook also contains an OpenCV webcam implementation.

The intended workflow is:

Webcam
  ↓
Capture Frame
  ↓
Flip Horizontally
  ↓
Convert BGR → RGB
  ↓
Resize 256×256
  ↓
Normalize
  ↓
Xception Model
  ↓
Prediction
  ↓
Confidence
  ↓
OpenCV Overlay

The webcam uses:

cv2.VideoCapture(0)

and displays prediction information over the camera frame.

24. Webcam Interface Features

The OpenCV interface displays:

Predicted rainfall category
Confidence percentage
Probability bar for each class
Color-coded status

The intended colors are:

Category	Color
No-to-Low Rain	Green
Low-to-Medium Rain	Yellow
Medium-to-Heavy Rain	Red

25. Current System Workflow

For your report, we can document the existing system as:

CCSN Dataset
      ↓
Cloud Images
      ↓
Rainfall Category Mapping
      ↓
Data Augmentation
      ↓
Image Normalization
      ↓
Xception Transfer Learning
      ↓
Phase 1 Training
      ↓
Xception Fine-Tuning
      ↓
Trained Model
      ↓
 ┌───────────────┬─────────────────┐
 ↓               ↓                 ↓
Image Upload    Gradio          Webcam
Prediction      Interface       Prediction
 ↓               ↓                 ↓
Rainfall        Rainfall        Rainfall
Category        Probabilities   Category
26. Current Technology Stack

This is another table you can directly put into your report.

Component	Technology
Programming Language	Python
Development Platform	Google Colab
Deep Learning	TensorFlow / Keras
CNN Architecture	Xception
Transfer Learning	ImageNet pretrained weights
Dataset	CCSN
Dataset Download	KaggleHub
Image Processing	OpenCV
Data Augmentation	Keras ImageDataGenerator
Numerical Processing	NumPy
Visualization	Matplotlib
Web UI	Gradio
Model Format	Keras .keras / HDF5 .h5
Hardware during training	Google Colab NVIDIA T4 GPU

These technologies are directly supported by the notebook.

27. Current System Advantages

These are supported by what the notebook actually implements:

Transfer Learning

The system uses an ImageNet-pretrained Xception model rather than training a CNN from scratch.

Data Augmentation

Multiple augmentation techniques are used during training.

Fine-Tuning

The pretrained Xception network is subsequently unfrozen and fine-tuned using a small learning rate.

Multiple Interfaces

The model can be used through:

Individual image prediction
Gradio interface
Webcam interface

28. Current Limitations — VERY IMPORTANT

These should go into our Day 2 technical analysis, but we should eventually fix them.

Limitation 1 — No Independent Test Dataset

The notebook uses:

80% training
20% validation

There is no independent test dataset.

Therefore, the current notebook does not provide a true final test accuracy.

Limitation 2 — Validation Augmentation

The same ImageDataGenerator containing augmentation is used to create both training and validation generators.

That means the validation pipeline also inherits the augmentation configuration.

For the final research version, we should create:

Training:
augmentation + normalization

Validation:
normalization only

Test:
normalization only

This is one of the first things we'll correct.