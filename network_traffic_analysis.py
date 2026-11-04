import os
import pandas as pd
import matplotlib.pyplot as plt

# Locate the existing dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "datasets", "my_data.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "network_traffic_results")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load dataset
df = pd.read_csv(DATASET_PATH)

print("=" * 60)
print("MEDSECURE SENTINEL - NETWORK TRAFFIC ANALYSIS")
print("=" * 60)

print(f"\nDataset rows: {df.shape[0]}")
print(f"Dataset columns: {df.shape[1]}")

print("\nAvailable columns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum().sort_values(ascending=False).head(10))

# Identify useful columns automatically
attack_col = next(
    (c for c in df.columns if c.lower().replace("_", " ") == "attack category"),
    None
)

label_col = next(
    (c for c in df.columns if c.lower() == "label"),
    None
)

# Save dataset summary
summary = pd.DataFrame({
    "Column": df.columns,
    "Data Type": [str(dtype) for dtype in df.dtypes],
    "Missing Values": df.isnull().sum().values,
    "Unique Values": df.nunique().values
})
summary.to_csv(os.path.join(OUTPUT_DIR, "dataset_summary.csv"), index=False)

# Analyse attack categories
category_col = attack_col or label_col

if category_col:
    counts = df[category_col].fillna("Unknown").astype(str).value_counts()

    print(f"\nTraffic/attack distribution ({category_col}):")
    print(counts.to_string())

    counts.to_csv(
        os.path.join(OUTPUT_DIR, "traffic_category_counts.csv"),
        header=["Count"]
    )

    plt.figure(figsize=(10, 6))
    counts.plot(kind="bar")
    plt.title("Network Traffic / Attack Category Distribution")
    plt.xlabel("Category")
    plt.ylabel("Number of Records")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "traffic_category_distribution.png"))
    plt.close()
else:
    print("\nNo recognised attack-category or label column was found.")

# Analyse numeric network traffic features
numeric_df = df.select_dtypes(include="number")
numeric_df.describe().T.to_csv(
    os.path.join(OUTPUT_DIR, "numeric_traffic_statistics.csv")
)

print("\nNumeric traffic statistics:")
print(numeric_df.describe().round(2).to_string())

# Generate a correlation graph for numeric features
if numeric_df.shape[1] >= 2:
    correlation = numeric_df.corr()
    correlation.to_csv(
        os.path.join(OUTPUT_DIR, "feature_correlation.csv")
    )

    plt.figure(figsize=(12, 9))
    plt.imshow(correlation, aspect="auto", vmin=-1, vmax=1)
    plt.colorbar(label="Correlation")
    plt.xticks(range(len(correlation.columns)), correlation.columns,
               rotation=90, fontsize=7)
    plt.yticks(range(len(correlation.index)), correlation.index,
               fontsize=7)
    plt.title("Correlation Between Numeric Dataset Features")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "feature_correlation.png"))
    plt.close()

print("\nAnalysis completed!")
print(f"Results saved in: {OUTPUT_DIR}")
print("\nNote: This analyses existing dataset records; it does not capture live traffic.")
