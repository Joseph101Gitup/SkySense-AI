# Baseline AI Model Analysis

## Existing Model

Xception-based transfer learning model.

## Dataset

CCSN dataset mapped into three rainfall categories.

## Total Images

2543

## Original Training Images

2036

## Original Validation Images

507

## Input Resolution

256 × 256 × 3

## Batch Size

32

## Number of Classes

3

## Phase 1

Frozen Xception backbone.

Training epochs: 30

Final training accuracy: 70.38%

Final validation accuracy: 55.82%

Best validation accuracy: 57.99%

## Phase 2

Full Xception fine-tuning.

Training epochs: 30

Learning rate: 0.00001

Final training accuracy: 91.06%

Final validation accuracy: 61.74%

Best validation accuracy: 62.13%

## Observed Issue

A substantial training-validation performance gap exists,
indicating potential overfitting and/or dataset/generalization
limitations.

## Verification Required

- Class distribution
- Class-index mapping
- Correct validation preprocessing
- Independent test set
- Confusion matrix
- Precision
- Recall
- F1-score