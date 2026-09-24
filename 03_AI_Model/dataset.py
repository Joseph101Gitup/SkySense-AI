import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.dataset import *

if __name__ == "__main__":
    src = locate_or_download_ccsn()
    prepare_processed_dataset(src)
    create_stratified_splits()
    get_data_generators()
