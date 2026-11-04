
import json
from pathlib import Path

import matplotlib.pyplot as plt

# Project report files
PROJECT_DIR = Path(__file__).resolve().parent  # originally D:\MedSecure-ML
REPORT_DIR = PROJECT_DIR / "output" / "reports"
INPUT_FILE = REPORT_DIR / "classification_report.json"
OUTPUT_FILE = REPORT_DIR / "simulation_results_table.png"

# Read the existing CNN evaluation results
with open(INPUT_FILE, "r", encoding="utf-8") as file:
    report = json.load(file)

# Extract the recorded values
rows = [
    [
        "Precision",
        f'{report["Attack"]["precision"] * 100:.2f}%',
        f'{report["Benign"]["precision"] * 100:.2f}%',
        f'{report["macro avg"]["precision"] * 100:.2f}%'
    ],
    [
        "Recall",
        f'{report["Attack"]["recall"] * 100:.2f}%',
        f'{report["Benign"]["recall"] * 100:.2f}%',
        f'{report["macro avg"]["recall"] * 100:.2f}%'
    ],
    [
        "F1-score",
        f'{report["Attack"]["f1-score"] * 100:.2f}%',
        f'{report["Benign"]["f1-score"] * 100:.2f}%',
        f'{report["macro avg"]["f1-score"] * 100:.2f}%'
    ],
    [
        "Test samples",
        str(int(report["Attack"]["support"])),
        str(int(report["Benign"]["support"])),
        str(int(report["macro avg"]["support"]))
    ],
    [
        "Accuracy",
        "—",
        "—",
        f'{report["accuracy"] * 100:.2f}%'
    ]
]

# Create a clean results table image
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.axis("off")
ax.set_position([0.04, 0.20, 0.92, 0.58])

# Main title
fig.text(
    0.5, 0.95,
    "MedSecure Sentinel",
    ha="center",
    va="center",
    fontsize=21,
    fontweight="bold"
)

# Subtitle
fig.text(
    0.5, 0.89,
    "SmallCNN Classification Results — Held-out Image Test Set",
    ha="center",
    va="center",
    fontsize=12
)


table = ax.table(
    cellText=rows,
    colLabels=["Metric", "Attack", "Benign", "Macro average"],
    cellLoc="center",
    colLoc="center",
    loc="center",
    colWidths=[0.25, 0.22, 0.22, 0.28]
)

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 1.8)

# Style the header and row labels
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight="bold", color="white")
        cell.set_facecolor("#25476A")
    elif col == 0:
        cell.set_text_props(weight="bold")
        cell.set_facecolor("#EAF0F6")
    else:
        cell.set_facecolor("#F7F9FC")

    cell.set_edgecolor("#C8D2DC")

fig.text(
    0.5,
    0.035,
    "Accuracy: {:.2f}%  |  Total test images: {:,}".format(
        report["accuracy"] * 100,
        int(report["macro avg"]["support"])
    ),
    ha="center",
    fontsize=10
)

plt.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)
plt.close(fig)

print("Simulation results table generated successfully!")
print(f"Saved to: {OUTPUT_FILE}")
