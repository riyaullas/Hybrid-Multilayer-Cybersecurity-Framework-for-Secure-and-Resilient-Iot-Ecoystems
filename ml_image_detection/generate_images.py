import re
import json
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from config import (
    TRAIN_CSV, TEST_CSV, OUTPUT_DIR, IMAGE_DIR, REPORT_DIR,
    MAX_IMAGES_PER_SPLIT, LABEL_COLUMN, IMAGE_SIDE, RANDOM_STATE
)

LABEL_CANDIDATES = [
    "label", "class", "attack", "attack_type", "category",
    "traffic_label", "target", "type"
]
DROP_HINTS = ("timestamp", "flow id", "src ip", "dst ip", "source ip",
              "destination ip", "mac", "row id", "unnamed")

def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Copy the official dataset CSV to this path, "
            "or update TRAIN_CSV/TEST_CSV in config.py."
        )
    return pd.read_csv(path, low_memory=False)

def find_label_column(df):
    if LABEL_COLUMN:
        if LABEL_COLUMN not in df.columns:
            raise ValueError(f"LABEL_COLUMN={LABEL_COLUMN!r} not found. Columns: {list(df.columns)}")
        return LABEL_COLUMN
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for candidate in LABEL_CANDIDATES:
        if candidate in normalized:
            return normalized[candidate]
    # Fall back to common CIC-style label suffixes, but make the choice visible.
    for col in df.columns:
        name = str(col).strip().lower()
        if "label" in name or "attack" in name:
            return col
    raise ValueError(
        "Could not safely identify the label column. Set LABEL_COLUMN in config.py. "
        f"Available columns: {list(df.columns)}"
    )

def clean_name(value):
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text[:70] or "unknown"


def numeric_feature_columns(df, label_col):
    cols = []
    excluded = {
        str(label_col).strip().lower(),
        "label",
        "attack_type",
        "source_file",
    }

    for col in df.columns:
        if str(col).strip().lower() in excluded:
            continue

        lower = str(col).strip().lower()
        if any(hint in lower for hint in DROP_HINTS):
            continue

        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() > 0:
            cols.append(col)

    if not cols:
        raise ValueError("No usable numeric feature columns found.")

    return cols

    
def main():
    train_df = read_csv(TRAIN_CSV)
    test_df = read_csv(TEST_CSV)
    label_col = find_label_column(train_df)
    if label_col not in test_df.columns:
        raise ValueError(f"Test CSV has no label column {label_col!r}.")
    features = numeric_feature_columns(train_df, label_col)
    features = [c for c in features if c in test_df.columns]
    if len(features) < 4:
        raise ValueError(f"Only {len(features)} usable numeric features found; inspect the CSV.")

    # Normalize using training data only to prevent test-set leakage.
    x_train = train_df[features].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians)
    x_test = test_df[features].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(medians)
    scaler = MinMaxScaler()
    scaler.fit(x_train)
    x_train = scaler.transform(x_train)
    x_test = scaler.transform(x_test)

    train_labels = train_df[label_col].astype(str).str.strip().fillna("unknown")
    test_labels = test_df[label_col].astype(str).str.strip().fillna("unknown")

    # Image pixel mapping: normalized feature vector -> fixed 8x8 grayscale image.
    n_pixels = IMAGE_SIDE * IMAGE_SIDE

    def export_split(split, matrix, labels):
        out_count = 0
        counts = {}

        if MAX_IMAGES_PER_SPLIT is None:
            selected_indices = np.arange(len(matrix))
        else:
            rng = np.random.default_rng(RANDOM_STATE)
            labels_array = labels.astype(str).to_numpy()
            selected_indices = []

            classes = sorted(set(labels_array))
            per_class = max(1, MAX_IMAGES_PER_SPLIT // len(classes))

            for class_name in classes:
                class_indices = np.flatnonzero(labels_array == class_name)
                take = min(per_class, len(class_indices))
                if take:
                    selected_indices.extend(
                        rng.choice(class_indices, size=take, replace=False).tolist()
                    )

            selected_indices = sorted(selected_indices)

        for idx in selected_indices:
            label = clean_name(labels.iloc[idx])
            folder = IMAGE_DIR / split / label
            folder.mkdir(parents=True, exist_ok=True)
            vec = matrix[idx]

            if len(vec) < n_pixels:
                vec = np.pad(vec, (0, n_pixels - len(vec)))
            else:
                vec = vec[:n_pixels]

            pixels = np.clip(vec * 255, 0, 255).astype(np.uint8).reshape(IMAGE_SIDE, IMAGE_SIDE)
            filename = f"{split}_{idx:07d}.png"
            Image.fromarray(pixels, mode="L").save(folder / filename)

            rows.append({
                "split": split,
                "image_path": str((folder / filename).relative_to(OUTPUT_DIR)),
                "source_row_index": int(idx),
                "label": str(labels.iloc[idx])
            })
            counts[label] = counts.get(label, 0) + 1
            out_count += 1

        return out_count, counts
    
    rows = []
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    train_n, train_counts = export_split("train", x_train, train_labels)
    test_n, test_counts = export_split("test", x_test, test_labels)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "manifest.csv", index=False)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "label_column": str(label_col),
        "feature_columns_used": [str(c) for c in features],
        "image_dimensions": [IMAGE_SIDE, IMAGE_SIDE],
        "max_images_per_split": MAX_IMAGES_PER_SPLIT,
        "train_rows_exported": train_n, "test_rows_exported": test_n,
        "train_class_counts": train_counts, "test_class_counts": test_counts,
        "warning": "Preview images are for pipeline validation only when capped at 10."
    }
    (REPORT_DIR / "generation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nManifest: {OUTPUT_DIR / 'manifest.csv'}")

if __name__ == "__main__":
    main()
