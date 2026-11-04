
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = DATA / "binary_evaluation"

OUT.mkdir(parents=True, exist_ok=True)

ALLOWED = {
    "Benign",
    "ARP_Spoofing",
    "MQTT_DDoS_Connect_Flood",
}

for split in ["train", "test"]:
    source = DATA / f"{split}.csv"
    df = pd.read_csv(source, low_memory=False)

    filtered = df[df["attack_type"].isin(ALLOWED)].copy()

    if filtered.empty:
        raise ValueError(f"No rows remain in {split}")

    print(f"\n{split.upper()} rows: {len(filtered)}")
    print(filtered.groupby(["label", "attack_type"]).size().to_string())

    filtered.to_csv(OUT / f"{split}.csv", index=False)

print(f"\nSaved filtered datasets to: {OUT}")
print("Original CSV files were not modified.")
