import sys
from pathlib import Path

ai_dir = Path(r"D:\personal\SkySense_AI\03_AI_Model")
if str(ai_dir) not in sys.path:
    sys.path.insert(0, str(ai_dir))

from src import predict, config

predictor = predict.RainfallPredictor()
test_dir = config.TEST_DIR

for cls in config.CLASS_NAMES:
    cls_folder = test_dir / cls
    sample = next(cls_folder.glob("*.jpg"), None)
    if sample:
        res = predictor.predict(sample)
        print("=" * 60)
        print("Ground Truth Class:", cls)
        print("Image File        :", sample.name)
        print("Predicted Class   :", res["predicted_class"])
        print("Confidence        :", f"{res['confidence_percentage']:.2f}%")
        print("Probabilities     :", res["class_probabilities"])
        print("Risk Level        :", res["risk_level"])
        print("Advisory          :", res["recommended_action"])
