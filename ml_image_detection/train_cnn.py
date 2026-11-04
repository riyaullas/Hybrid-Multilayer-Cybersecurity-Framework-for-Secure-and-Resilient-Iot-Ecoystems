import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from config import IMAGE_DIR, REPORT_DIR, OUTPUT_DIR, IMAGE_SIDE

BATCH_SIZE = 32
EPOCHS = 8
LEARNING_RATE = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ImageFolderDataset(Dataset):
    def __init__(self, manifest, split, output_dir, class_to_idx):
        self.items = []
        self.class_to_idx = class_to_idx

        df = pd.read_csv(manifest)
        df = df[df["split"] == split]

        for _, row in df.iterrows():
            label_name = str(row["label"])
            if label_name not in class_to_idx:
                continue

            path = output_dir / str(row["image_path"])
            if not path.exists():
                raise FileNotFoundError(f"Missing image: {path}")

            self.items.append((path, class_to_idx[label_name]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        path, label = self.items[index]
        arr = np.asarray(
            Image.open(path).convert("L"), dtype=np.float32
        ) / 255.0

        return (
            torch.from_numpy(arr[None, :, :]),
            torch.tensor(label, dtype=torch.long)
        )


class SmallCNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2)), nn.Flatten(),
            nn.Linear(32 * 2 * 2, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, n_classes)
        )
    def forward(self, x):
        return self.net(x)

def classes_in(folder):
    return sorted(p.name for p in folder.iterdir() if p.is_dir())

def main():
    train_root, test_root = IMAGE_DIR / "train", IMAGE_DIR / "test"
    if not train_root.exists() or not test_root.exists():
        raise FileNotFoundError("Run generate_images.py first.")
    classes = sorted(set(classes_in(train_root)) | set(classes_in(test_root)))
    if len(classes) < 2:
        raise ValueError("Need at least two classes. Export the full dataset; 10 preview images may contain only one class.")
    class_to_idx = {name: i for i, name in enumerate(classes)}
    manifest_path = OUTPUT_DIR / "manifest.csv"
    train_ds = ImageFolderDataset(manifest_path, "train", OUTPUT_DIR, class_to_idx)
    test_ds = ImageFolderDataset(manifest_path, "test", OUTPUT_DIR, class_to_idx)

    print(f"Training images: {len(train_ds)}")
    print(f"Testing images: {len(test_ds)}")
    if len(train_ds) < 20 or len(test_ds) < 10:
        raise ValueError("Too few images for a meaningful CNN run. Set MAX_IMAGES_PER_SPLIT=None and regenerate images.")
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    model = SmallCNN(len(classes)).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        model.train()
        total_loss, seen = 0.0, 0
        for x, y in train_loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)
            seen += len(y)
        print(f"Epoch {epoch+1}/{EPOCHS} - loss: {total_loss/max(seen,1):.4f}")

    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in test_loader:
            logits = model(x.to(DEVICE))
            preds = logits.argmax(dim=1).cpu().numpy()
            y_pred.extend(preds.tolist())
            y_true.extend(y.numpy().tolist())

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = classification_report(
        y_true, y_pred, labels=list(range(len(classes))), target_names=classes,
        output_dict=True, zero_division=0
    )
    (REPORT_DIR / "classification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(classes))))
    disp = ConfusionMatrixDisplay(cm, display_labels=classes)
    fig, ax = plt.subplots(figsize=(max(6, len(classes)), max(5, len(classes))))
    disp.plot(ax=ax, xticks_rotation=45, colorbar=False)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "confusion_matrix.png", dpi=160)
    torch.save({"state_dict": model.state_dict(), "classes": classes, "image_side": IMAGE_SIDE},
               OUTPUT_DIR / "cnn_model.pt")
    print("Saved:", REPORT_DIR / "classification_report.json")
    print("Saved:", REPORT_DIR / "confusion_matrix.png")
    print("Saved:", OUTPUT_DIR / "cnn_model.pt")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
