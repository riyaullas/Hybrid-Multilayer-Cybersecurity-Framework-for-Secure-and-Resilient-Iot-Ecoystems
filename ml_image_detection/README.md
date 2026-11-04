> **Integration note:** this pipeline produced `backend/app/image_detection/cnn_model.pt`, which the app serves at `POST /api/v1/image-detection/predict` and on the *Image-Based Detection* page.
> The committed `config.py` is the final run's configuration (`MAX_IMAGES_PER_SPLIT = 5000`, train/test from `data/binary_evaluation/`). The original working copy lives in `D:\MedSecure-ML`.
> Recorded results are in `reports/`. Data (`data/`, `dataset_source/`) and generated images (`output/`) are not committed.

# MedSecure Sentinel — IoT Traffic-to-Image Starter

This is a non-destructive starter module. It does not modify your existing backend or frontend.

## Important
- The first run exports **up to 10 preview images** only to verify the conversion pipeline.
- Ten images are not enough to train or evaluate a credible CNN. After preview validation, change `MAX_IMAGES_PER_SPLIT` in `config.py` to `None` to export all usable rows.
- Use real labelled CICIoMT2024 CSV files. The generated PNGs are derived samples, not original medical images.
- Keep the source dataset's official train/test separation. Do not randomly mix rows from the same capture into both sets.
- Do not report metrics until a real training/evaluation run has completed.

## 1. Download the data
Download the extracted CSV files from the official CICIoMT2024 page:
https://www.unb.ca/cic/datasets/iomt-dataset-2024.html

Prefer the provided CSVs under the WiFi_and_MQTT attacks `csv` directory. Keep the official train and test files separate.

## 2. Place files
Create this structure inside your project root (`medsecure-sentinel`):

```text
ml_image_detection/
  config.py
  generate_images.py
  train_cnn.py
  requirements.txt
  data/
    train.csv
    test.csv
```

Copy the dataset's actual training CSV to `data/train.csv` and test CSV to `data/test.csv`. If the dataset provides multiple CSVs, initially select a compatible train/test pair and document the exact filenames.

## 3. Install dependencies
From a terminal in `ml_image_detection`:

Windows PowerShell:
```powershell
cd "C:\Users\MY PC\Documents\medsecure-sentinel\ml_image_detection"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

You can also use the backend virtual environment if you prefer, but keep ML dependencies separate at first to avoid breaking the running API.

## 4. Generate 10 preview images
```powershell
.\.venv\Scripts\python.exe generate_images.py
```
Review `output/images/train` and `output/images/test`. The script prints the selected label column, features, class counts and output count. Check `output/manifest.csv` to map each image back to its source row and label.

If the label column is not detected correctly, set `LABEL_COLUMN` explicitly in `config.py` to the exact column name printed by the script or shown in the CSV header.

## 5. Generate all images
After validating previews, open `config.py` and set:
```python
MAX_IMAGES_PER_SPLIT = None
```
Then delete only the generated `output/images` and `output/manifest.csv` folders/files, and rerun `generate_images.py`. Do not delete your original CSVs.

## 6. Train a baseline CNN
After full export:
```powershell
.\.venv\Scripts\python.exe train_cnn.py
```
The script trains a small CNN on the generated training images and evaluates the held-out test images. It saves metrics and a confusion matrix in `output/reports`.

## 7. Integration into MedSecure Sentinel
First run this as a standalone experiment. Do not wire it into the production API until the dataset, labels and model evaluation are verified. Later, expose a separate inference service/function that returns:
- predicted class
- attack probability (only if the model supports calibrated probabilities)
- model version
- timestamp and source record/flow identifier

The existing trust/risk engine can consume this result as one signal. It should not replace RSA/signature verification, behavioural monitoring, MITM checks, or firmware verification.

## Research cautions
- Fit normalization using training data only; this starter script does so.
- Use the original test split where available.
- Never include labels as image features.
- Remove identifiers that cause leakage (for example capture-specific IDs); review columns before final experiments.
- Report class-wise precision/recall/F1, macro-F1, confusion matrix and false-positive rate, not accuracy alone.
- Image conversion is a representation choice, not a guaranteed improvement. Compare against a tabular baseline on the same split.
