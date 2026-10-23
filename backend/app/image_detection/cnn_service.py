from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn

MODEL_PATH = Path(__file__).resolve().parent / "cnn_model.pt"
DEVICE = torch.device("cpu")


class SmallCNN(nn.Module):
    def __init__(self, n_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2)),
            nn.Flatten(),
            nn.Linear(32 * 2 * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.net(x)


checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=False,
)
CLASSES = checkpoint["classes"]
IMAGE_SIDE = int(checkpoint["image_side"])

model = SmallCNN(len(CLASSES)).to(DEVICE)
model.load_state_dict(checkpoint["state_dict"])
model.eval()


def predict_image(image: Image.Image) -> dict:
    image = image.convert("L")

    if image.size != (IMAGE_SIDE, IMAGE_SIDE):
        raise ValueError(
            f"Please upload a generated {IMAGE_SIDE}x{IMAGE_SIDE} "
            "traffic-representation image."
        )

    array = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array[None, None, :, :]).to(DEVICE)

    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1)[0]

    scores = {
        label: round(float(probabilities[i].item()) * 100, 2)
        for i, label in enumerate(CLASSES)
    }
    best_index = int(probabilities.argmax().item())

    return {
        "prediction": CLASSES[best_index],
        "confidence": scores[CLASSES[best_index]],
        "probabilities": scores,
        "model": "SmallCNN",
        "image_size": f"{IMAGE_SIDE}x{IMAGE_SIDE}",
        "note": (
            "Experimental classifier trained on generated network-traffic "
            "representations. This prediction is not proof of a real attack."
        ),
    }
