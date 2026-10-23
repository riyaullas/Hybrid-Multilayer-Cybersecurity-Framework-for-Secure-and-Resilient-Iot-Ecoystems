from pathlib import Path
import torch
from torch import nn
from PIL import Image
import numpy as np

MODEL_PATH = Path("backend/app/image_detection/cnn_model.pt")
IMAGE_ROOT = Path(r"D:\MedSecure-ML\output\images")

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

checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
classes = checkpoint["classes"]
model = SmallCNN(len(classes))
model.load_state_dict(checkpoint["state_dict"])
model.eval()

print("Model loaded successfully")
print("Classes:", classes)
print("Expected image size:", checkpoint["image_side"], "x", checkpoint["image_side"])

images = list(IMAGE_ROOT.glob("test/*/*.png"))
if not images:
    raise FileNotFoundError(f"No generated test images found under {IMAGE_ROOT}")

image_path = images[0]
with Image.open(image_path) as img:
    arr = np.asarray(img.convert("L"), dtype=np.float32) / 255.0

if arr.shape != (8, 8):
    raise ValueError(f"Expected an 8x8 image, got {arr.shape}")

x = torch.from_numpy(arr[None, None, :, :])
with torch.no_grad():
    probabilities = torch.softmax(model(x), dim=1)[0]
    index = int(probabilities.argmax())

print("Test image:", image_path)
print("Predicted class:", classes[index])
print("Model confidence:", f"{probabilities[index].item() * 100:.2f}%")
