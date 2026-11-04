from pathlib import Path
import json

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_DIR / "datasets" / "my_data.csv"
MODEL_PATH = PROJECT_DIR / "ml_model" / "medsecure_model.joblib"
RESULTS_DIR = PROJECT_DIR / "ml_model" / "model_comparison_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20
TARGET_COLUMN = "Attack Category"


def make_preprocessor(numeric_cols, categorical_cols, scale_numeric=False):
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(numeric_steps)

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_cols),
        ("categorical", categorical_pipeline, categorical_cols),
    ])


def main():
    print("=" * 65)
    print("MEDSECURE SENTINEL - RANDOM FOREST vs SVM")
    print("=" * 65)

    df = pd.read_csv(DATASET_PATH)
    print(f"\nDataset loaded: {df.shape[0]} records, {df.shape[1]} columns")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' was not found.")

    df = df.dropna(subset=[TARGET_COLUMN]).copy()
    y = df[TARGET_COLUMN].astype(str)

    columns_to_drop = [
        TARGET_COLUMN, "Label", "SrcAddr", "DstAddr", "SrcMac", "DstMac",
    ]
    X = df.drop(columns=[c for c in columns_to_drop if c in df.columns])

    all_missing = X.columns[X.isna().all()].tolist()
    if all_missing:
        print(f"Dropping entirely empty feature columns: {all_missing}")
        X = X.drop(columns=all_missing)
    if X.shape[1] == 0:
        raise ValueError("No usable feature columns remain.")

    categorical_cols = X.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()
    numeric_cols = X.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()

    unclassified_cols = [
        c for c in X.columns if c not in categorical_cols and c not in numeric_cols
    ]
    if unclassified_cols:
        X[unclassified_cols] = X[unclassified_cols].astype("string")
        categorical_cols.extend(unclassified_cols)

    print(f"Features used: {X.shape[1]}")
    print(f"Numeric features: {len(numeric_cols)}")
    print(f"Categorical features: {len(categorical_cols)}")
    print("\nClass distribution:")
    print(y.value_counts().to_string())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"\nTraining records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    models = {
        "Random Forest": Pipeline([
            ("preprocessor", make_preprocessor(numeric_cols, categorical_cols)),
            ("classifier", RandomForestClassifier(
                n_estimators=100,
                random_state=RANDOM_STATE,
                class_weight="balanced",
                n_jobs=-1,
            )),
        ]),
        "SVM": Pipeline([
            ("preprocessor", make_preprocessor(
                numeric_cols, categorical_cols, scale_numeric=True
            )),
            ("classifier", SVC(
                kernel="rbf",
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
        ]),
    }

    results = []
    predictions_by_model = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        predictions_by_model[name] = predictions

        metrics = {
            "Model": name,
            "Accuracy": accuracy_score(y_test, predictions),
            "Precision": precision_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
            "Recall": recall_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
            "F1 Score": f1_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
        }
        results.append(metrics)

        print("\n" + "-" * 65)
        print(f"{name} evaluation")
        print("-" * 65)
        for metric in ["Accuracy", "Precision", "Recall", "F1 Score"]:
            print(f"{metric}: {metrics[metric]:.4f}")
        print("\nClassification report:")
        print(classification_report(y_test, predictions, zero_division=0))
        print("Confusion matrix (class order):")
        print(model.named_steps["classifier"].classes_)
        print(confusion_matrix(
            y_test, predictions,
            labels=model.named_steps["classifier"].classes_,
        ))

    results_df = pd.DataFrame(results)
    csv_path = RESULTS_DIR / "random_forest_vs_svm_metrics.csv"
    json_path = RESULTS_DIR / "random_forest_vs_svm_metrics.json"
    results_df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Grouped bar graph: the four metrics for both models.
    metric_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
    ax = results_df.set_index("Model")[metric_names].T.plot(
        kind="bar", figsize=(10, 6), width=0.78
    )
    ax.set_title("Random Forest vs SVM - Held-out Test Metrics")
    ax.set_xlabel("Evaluation metric")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticklabels(metric_names, rotation=0)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(title="Model")
    plt.tight_layout()
    graph_path = RESULTS_DIR / "random_forest_vs_svm_comparison.png"
    plt.savefig(graph_path, dpi=200, bbox_inches="tight")
    plt.close()

    # Save SVM separately, and keep the existing Random Forest artifact format.
    svm_path = PROJECT_DIR / "ml_model" / "medsecure_svm_model.joblib"
    joblib.dump({
        "model": models["SVM"],
        "feature_columns": X.columns.tolist(),
        "classes": models["SVM"].named_steps["classifier"].classes_.tolist(),
        "target_column": TARGET_COLUMN,
        "random_state": RANDOM_STATE,
    }, svm_path)

    joblib.dump({
        "model": models["Random Forest"],
        "feature_columns": X.columns.tolist(),
        "classes": models["Random Forest"].named_steps["classifier"].classes_.tolist(),
    }, MODEL_PATH)

    print("\n" + "=" * 65)
    print("COMPARISON COMPLETE")
    print("=" * 65)
    print("\nMetrics summary (scores from 0 to 1):")
    print(results_df.to_string(index=False, formatters={
        "Accuracy": "{:.4f}".format,
        "Precision": "{:.4f}".format,
        "Recall": "{:.4f}".format,
        "F1 Score": "{:.4f}".format,
    }))
    print(f"\nMetrics CSV: {csv_path}")
    print(f"Metrics JSON: {json_path}")
    print(f"Bar graph:   {graph_path}")
    print(f"SVM model:   {svm_path}")
    print(f"Random Forest model saved to: {MODEL_PATH}")
    print("\nNote: weighted precision, recall, and F1 are used for this "
          "three-class classification task. Results are from this dataset's "
          "held-out test split and do not guarantee real-world performance.")


if __name__ == "__main__":
    main()
