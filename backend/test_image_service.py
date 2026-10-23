from pathlib import Path
from PIL import Image
from app.image_detection.cnn_service import predict_image

image_path = Path(r"D:\MedSecure-ML\output\images\test\Attack\test_0000021.png")

with Image.open(image_path) as image:
    result = predict_image(image)

print(result)
