from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

ROOT = Path(__file__).resolve().parent  # originally D:\MedSecure-ML
DATA = ROOT / "data" / "binary_evaluation" / "test.csv"
MODEL_DIR = ROOT.parent / "backend" / "app" / "network_model"
OUT = ROOT / "output" / "tabular_experiment" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

if not DATA.exists():
    raise FileNotFoundError(f"Test dataset not found: {DATA}")

model = joblib.load(MODEL_DIR / "random_forest.joblib")
preprocessing = joblib.load(MODEL_DIR / "preprocessing.joblib")
features = preprocessing["features"]
imputer = preprocessing["imputer"]

df = pd.read_csv(DATA)
if "label" not in df.columns:
    raise ValueError(f"No 'label' column. Available columns: {list(df.columns)}")

missing = [c for c in features if c not in df.columns]
if missing:
    raise ValueError(f"Missing model features: {missing}")

X = df[features].apply(pd.to_numeric, errors="coerce")
y = df["label"].astype(str).str.strip()

valid = y.isin(["Attack", "Benign"])
X, y = X.loc[valid], y.loc[valid]

if X.empty:
    raise ValueError(f"No Attack/Benign labels found. Labels: {df['label'].value_counts().to_dict()}")

X = X.replace([float("inf"), float("-inf")], float("nan"))
X_transformed = imputer.transform(X)
predictions = model.predict(X_transformed)

labels = ["Attack", "Benign"]
report = classification_report(
    y, predictions, labels=labels, output_dict=True, zero_division=0
)
cm = confusion_matrix(y, predictions, labels=labels)

results = {
    "dataset": str(DATA),
    "test_rows_evaluated": int(len(y)),
    "features_used": int(len(features)),
    "accuracy": float(accuracy_score(y, predictions)),
    "classification_report": report,
    "confusion_matrix_labels_order": labels,
    "confusion_matrix": cm.tolist(),
    "note": "Evaluation on the prepared test CSV. Interpret as an independent test only if its separation from training data is verified."
}

report_path = OUT / "network_detector_test_validation.json"
report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\n=== NETWORK DETECTOR TEST VALIDATION ===")
print(f"Rows evaluated: {len(y):,}")
print(f"Features: {len(features)}")
print(f"Accuracy: {results['accuracy']:.4%}")
print("\nClassification report:")
print(classification_report(y, predictions, labels=labels, zero_division=0))
print("Confusion matrix (rows=true, columns=predicted; Attack, Benign):")
print(cm)
print(f"\nSaved report: {report_path}")
