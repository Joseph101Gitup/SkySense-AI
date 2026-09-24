import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.model import *

if __name__ == "__main__":
    m, b = build_model()
    compile_model(m, learning_rate=1e-3)
    print(get_model_summary_str(m))
