from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent  # originally D:\MedSecure-ML
root = ROOT / "data" / "binary_evaluation"
train_path = root / "train.csv"
test_path = root / "test.csv"

train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

features = [
    "Header_Length", "Protocol Type", "Duration", "Rate", "Srate",
    "Drate", "fin_flag_number", "syn_flag_number", "rst_flag_number",
    "psh_flag_number", "ack_flag_number", "ece_flag_number",
    "cwr_flag_number", "ack_count", "syn_count", "fin_count", "rst_count",
    "HTTP", "HTTPS", "DNS", "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP",
    "DHCP", "ARP", "ICMP", "IGMP", "IPv", "LLC", "Tot sum", "Min", "Max",
    "AVG", "Std", "Tot size", "IAT", "Number", "Magnitue", "Radius",
    "Covariance", "Variance", "Weight"
]

missing_train = [c for c in features if c not in train.columns]
missing_test = [c for c in features if c not in test.columns]
if missing_train or missing_test:
    raise ValueError(f"Missing train columns: {missing_train}; test columns: {missing_test}")

train_rows = train[features].copy()
test_rows = test[features].copy()

train_hashes = pd.util.hash_pandas_object(train_rows, index=False)
test_hashes = pd.util.hash_pandas_object(test_rows, index=False)

train_unique = set(train_hashes.tolist())
test_unique = set(test_hashes.tolist())
overlap_hashes = train_unique.intersection(test_unique)

result = {
    "train_rows": len(train),
    "test_rows": len(test),
    "train_unique_feature_rows": len(train_unique),
    "test_unique_feature_rows": len(test_unique),
    "shared_unique_feature_row_hashes": len(overlap_hashes),
    "warning": "Hash overlap is a screening check, not proof of leakage. Review source split methodology and verify any matches before drawing conclusions."
}

out = ROOT / "output" / "tabular_experiment" / "reports"
out.mkdir(parents=True, exist_ok=True)
report_path = out / "train_test_overlap_audit.json"
report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

print(json.dumps(result, indent=2))
print(f"\nSaved: {report_path}")
