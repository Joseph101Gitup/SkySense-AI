"""
SKYsense AI - Root Prediction Command-Line Tool
Usage:
    python predict.py path/to/image.jpg
"""

import sys
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.predict import main

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Usage: python predict.py <path_to_image.jpg>")
        sys.exit(1)
