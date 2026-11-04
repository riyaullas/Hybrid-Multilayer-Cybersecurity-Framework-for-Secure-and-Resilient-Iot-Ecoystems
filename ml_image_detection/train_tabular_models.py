
from pathlib import Path
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "binary_evaluation"
OUT_DIR = ROOT / "output" / "tabular_experiment"
MODEL_DIR = OUT_DIR / "models"
REPORT_DIR = OUT_DIR / "reports"

RANDOM_STATE = 42
RFE_SAMPLE_SIZE = 50000
RFE_FEATURES = 20


def load_data(path):
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")
    return pd.read_csv(path, low_memory=False)


def get_features(train, test):
    excluded = {"label", "attack_type", "source_file"}
    columns = []

    for col in train.columns:
        if str(col).strip().lower() in excluded:
            continue
        if col not in test.columns:
            continue

        values = pd.to_numeric(train[col], errors="coerce")
        if values.notna().any():
            columns.append(col)

    if len(columns) < 2:
        raise ValueError("Too few numeric feature columns were found.")

    return columns


def prepare_matrix(df, columns, imputer=None):
    frame = (
        df[columns]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
    )
    if imputer is None:
        imputer = SimpleImputer(strategy="median")
        matrix = imputer.fit_transform(frame)
    else:
        matrix = imputer.transform(frame)
    return matrix, imputer


def save_evaluation(name, model, x_test, y_test, classes):
    predictions = model.predict(x_test)

    results = {
        "model": name,
        "test_samples": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision_macro": float(
            precision_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=classes,
            target_names=[str(c) for c in classes],
            output_dict=True,
            zero_division=0,
        ),
    }

    safe_name = name.lower().replace(" ", "_").replace("+", "plus")
    (REPORT_DIR / f"{safe_name}_metrics.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    cm = confusion_matrix(y_test, predictions, labels=classes)
    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=[str(c) for c in classes],
    )
    display.plot(values_format="d")
    plt.title(f"{name} - Test Confusion Matrix")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / f"{safe_name}_confusion_matrix.png", dpi=160)
    plt.close()

    return {
        "model": name,
        "test_samples": len(y_test),
        "accuracy": results["accuracy"],
        "precision_macro": results["precision_macro"],
        "recall_macro": results["recall_macro"],
        "f1_macro": results["f1_macro"],
    }


def main():
    start = time.time()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading prepared datasets...")
    train_df = load_data(DATA_DIR / "train.csv")
    test_df = load_data(DATA_DIR / "test.csv")

    if "label" not in train_df.columns or "label" not in test_df.columns:
        raise ValueError("Both CSVs must contain a 'label' column.")

    y_train = train_df["label"].astype(str).str.strip().to_numpy()
    y_test = test_df["label"].astype(str).str.strip().to_numpy()

    if set(y_train) != set(y_test):
        raise ValueError(
            f"Train/test classes differ. Train={set(y_train)}, Test={set(y_test)}"
        )

    classes = sorted(set(y_train))
    print(f"Training rows: {len(y_train):,}")
    print(f"Testing rows:  {len(y_test):,}")
    print(f"Classes: {classes}")

    features = get_features(train_df, test_df)
    print(f"Numeric features: {len(features)}")

    x_train, imputer = prepare_matrix(train_df, features)
    x_test, _ = prepare_matrix(test_df, features, imputer)

    joblib.dump(
        {"features": features, "imputer": imputer},
        MODEL_DIR / "preprocessing.joblib",
    )

    comparison = []

    print("\nTraining Random Forest baseline...")
    rf = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(x_train, y_train)
    joblib.dump(rf, MODEL_DIR / "random_forest.joblib")

    comparison.append(
        save_evaluation("Random Forest", rf, x_test, y_test, classes)
    )
    print("Random Forest evaluation saved.")

    print("\nSelecting features with RFE on training data only...")
    rng = np.random.default_rng(RANDOM_STATE)
    sample_size = min(RFE_SAMPLE_SIZE, len(y_train))
    sample_indices = rng.choice(len(y_train), size=sample_size, replace=False)

    selector_estimator = RandomForestClassifier(
        n_estimators=40,
        max_depth=12,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    selector = RFE(
        estimator=selector_estimator,
        n_features_to_select=min(RFE_FEATURES, len(features)),
        step=0.2,
    )
    selector.fit(x_train[sample_indices], y_train[sample_indices])

    selected_features = [
        feature
        for feature, selected in zip(features, selector.support_)
        if selected
    ]
    (REPORT_DIR / "selected_features.json").write_text(
        json.dumps(selected_features, indent=2), encoding="utf-8"
    )
    joblib.dump(selector, MODEL_DIR / "rfe_selector.joblib")
    print(f"Selected {len(selected_features)} features: {selected_features}")

    selected_indices = [
        index for index, selected in enumerate(selector.support_) if selected
    ]
    x_train_selected = x_train[:, selected_indices]
    x_test_selected = x_test[:, selected_indices]

    print("\nTraining MLP with RFE-selected features...")
    mlp = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=512,
            learning_rate_init=0.001,
            max_iter=40,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=5,
            random_state=RANDOM_STATE,
            verbose=True,
        )),
    ])
    mlp.fit(x_train_selected, y_train)
    joblib.dump(
        {"model": mlp, "features": selected_features},
        MODEL_DIR / "rfe_mlp.joblib",
    )

    comparison.append(
        save_evaluation(
            "RFE + MLP", mlp, x_test_selected, y_test, classes
        )
    )

    comparison_df = pd.DataFrame(comparison)
    comparison_df.to_csv(REPORT_DIR / "model_comparison.csv", index=False)

    summary = {
        "dataset": "CICIoMT2024 filtered Wi-Fi/MQTT binary subset",
        "random_state": RANDOM_STATE,
        "training_samples": int(len(y_train)),
        "testing_samples": int(len(y_test)),
        "original_numeric_feature_count": len(features),
        "rfe_selected_feature_count": len(selected_features),
        "selected_features": selected_features,
        "classes": classes,
        "models": comparison,
        "elapsed_seconds": round(time.time() - start, 2),
        "notes": [
            "RFE was fitted using a random subset of training data only.",
            "The test set was not used for feature selection or model fitting.",
            "Results apply only to the selected binary dataset and its split.",
        ],
    }
    (REPORT_DIR / "experiment_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("\nMODEL COMPARISON")
    print(comparison_df.to_string(index=False))
    print(f"\nAll outputs saved to: {OUT_DIR}")
    print("Experiment completed.")


if __name__ == "__main__":
    main()
