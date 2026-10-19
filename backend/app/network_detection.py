
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / "network_model"
MODEL_PATH = MODEL_DIR / "random_forest.joblib"
PREPROCESS_PATH = MODEL_DIR / "preprocessing.joblib"

if not MODEL_PATH.exists() or not PREPROCESS_PATH.exists():
    raise RuntimeError(
        "Network detector model files are missing. "
        "Copy the trained model artifacts into app/network_model."
    )

model = joblib.load(MODEL_PATH)
preprocessing = joblib.load(PREPROCESS_PATH)

FEATURES = preprocessing["features"]
imputer = preprocessing["imputer"]


def predict_network_traffic(sample: dict):
    missing = [feature for feature in FEATURES if feature not in sample]
    if missing:
        raise ValueError(
            "Missing required network features: " + ", ".join(missing)
        )

    try:
        frame = pd.DataFrame(
            [[float(sample[feature]) for feature in FEATURES]],
            columns=FEATURES,
        )
    except (TypeError, ValueError):
        raise ValueError("Every feature must be a numeric value.")

    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Features must contain finite numeric values.")

    transformed = imputer.transform(frame)
    prediction = str(model.predict(transformed)[0])

    probabilities = None
    if hasattr(model, "predict_proba"):
        probabilities = {
            str(label): round(float(prob), 6)
            for label, prob in zip(
                model.classes_, model.predict_proba(transformed)[0]
            )
        }

    return {
        "classification": prediction,
        "model": "RandomForest-CICIoMT2024",
        "feature_count": len(FEATURES),
        "probabilities": probabilities,
        "synthetic": False,
        "warning": (
            "Research prototype. Supply the same numeric network-flow "
            "features and units used during training. Output is not a "
            "guarantee of compromise or a calibrated risk probability."
        ),
    }
