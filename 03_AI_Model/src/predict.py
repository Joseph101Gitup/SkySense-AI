"""
SKYsense AI - Command-Line Prediction Interface
Uses the production inference service to predict rainfall categories from cloud images.
Usage:
    python predict.py path/to/image.jpg
"""

import sys
import argparse
from pathlib import Path

# Add src to path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from inference import RainfallInferenceService, InferenceError


def main():
    parser = argparse.ArgumentParser(description="SKYsense AI - Cloud Image Rainfall Classification")
    parser.add_argument("image_path", type=str, help="Path to cloud image (.jpg, .jpeg, .png)")
    parser.add_argument("--model", type=str, default=None, help="Optional model path (.keras or .tflite)")
    args = parser.parse_args()

    try:
        service = RainfallInferenceService.get_instance(model_path=args.model)
        result = service.predict(args.image_path)

        print(f"Prediction: {result['predicted_class']}")
        print(f"Confidence: {result['confidence'] * 100:.2f}% ({result['confidence']:.4f})")
        print("All class probabilities:")
        for cls_name, prob in result["probabilities"].items():
            print(f"  {cls_name}: {prob * 100:.2f}% ({prob:.4f})")

    except (InferenceError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Usage: python predict.py <path_to_image.jpg>")
        sys.exit(1)
