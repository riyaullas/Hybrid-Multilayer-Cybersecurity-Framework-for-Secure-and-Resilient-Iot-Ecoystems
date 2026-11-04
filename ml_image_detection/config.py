from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
IMAGE_DIR = OUTPUT_DIR / "images"
REPORT_DIR = OUTPUT_DIR / "reports"

TRAIN_CSV = DATA_DIR / "binary_evaluation" / "train.csv"
TEST_CSV = DATA_DIR / "binary_evaluation" / "test.csv"

# Run a small smoke test first. Set to None only after checking preview images.
MAX_IMAGES_PER_SPLIT = 5000

# If auto-detection selects the wrong target, set this to the exact CSV column name.
LABEL_COLUMN = None

IMAGE_SIDE = 8  # 8x8 = 64 feature values per image
RANDOM_STATE = 42
