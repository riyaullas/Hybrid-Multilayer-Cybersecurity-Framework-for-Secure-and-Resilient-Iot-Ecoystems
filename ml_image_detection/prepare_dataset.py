
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "dataset_source"
OUTPUT = ROOT / "data"

OUTPUT.mkdir(parents=True, exist_ok=True)


def load_split(split_name):
    folder = SOURCE / split_name
    files = sorted(folder.glob("*.csv"))

    if not files:
        raise FileNotFoundError(f"No CSV files found in {folder}")

    frames = []

    for file in files:
        print(f"Reading: {file.name}")

        df = pd.read_csv(file, low_memory=False)

        # These dataset files have labels documented by their filenames.
        name = file.name.lower()

        if "benign" in name:
            label = "Benign"
            attack_type = "Benign"
        elif "arp_spoofing" in name:
            label = "Attack"
            attack_type = "ARP_Spoofing"
        elif "mqtt-ddos-connect_flood" in name:
            label = "Attack"
            attack_type = "MQTT_DDoS_Connect_Flood"
        elif "mqtt-dos-connect_flood" in name:
            label = "Attack"
            attack_type = "MQTT_DoS_Connect_Flood"
        else:
            raise ValueError(
                f"Unrecognised filename; refusing to guess its label: {file.name}"
            )

        df["label"] = label
        df["attack_type"] = attack_type
        df["source_file"] = file.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    if combined.empty:
        raise ValueError(f"No records found in {split_name}")

    return combined


def main():
    train = load_split("train")
    test = load_split("test")

    # Ensure the original feature schemas match before saving.
    train_features = [
        c for c in train.columns
        if c not in {"label", "attack_type", "source_file"}
    ]
    test_features = [
        c for c in test.columns
        if c not in {"label", "attack_type", "source_file"}
    ]

    if train_features != test_features:
        raise ValueError("Train and test feature columns do not match.")

    for name, df in [("train", train), ("test", test)]:
        print(f"\n{name.upper()} label counts:")
        print(df["label"].value_counts().to_string())

        print(f"\n{name.upper()} attack categories:")
        print(df["attack_type"].value_counts().to_string())

        numeric = df[train_features].apply(pd.to_numeric, errors="coerce")
        print("Non-numeric/missing feature values:", int(numeric.isna().sum().sum()))

    train.to_csv(OUTPUT / "train.csv", index=False)
    test.to_csv(OUTPUT / "test.csv", index=False)

    print("\nSaved processed files:")
    print(OUTPUT / "train.csv")
    print(OUTPUT / "test.csv")
    print("\nOriginal source CSVs were not modified.")


if __name__ == "__main__":
    main()
