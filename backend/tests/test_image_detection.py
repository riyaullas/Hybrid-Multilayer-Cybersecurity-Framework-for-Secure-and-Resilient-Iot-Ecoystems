"""Tests for the CNN image-based traffic detection module and its API route."""
import io
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.image_detection.cnn_service import CLASSES, IMAGE_SIDE, predict_image

FIXTURES = Path(__file__).parent / 'fixtures'
# Real generated CICIoMT2024 test-split images (from ml_image_detection/generate_images.py).
SAMPLES = {'Attack': FIXTURES / 'cnn_attack_sample.png', 'Benign': FIXTURES / 'cnn_benign_sample.png'}


def png_bytes(image: Image.Image, fmt: str = 'PNG') -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


# ---------------------------------------------------------------- service

def test_cnn_checkpoint_metadata():
    assert CLASSES == ['Attack', 'Benign']
    assert IMAGE_SIDE == 8


@pytest.mark.parametrize('label', ['Attack', 'Benign'])
def test_cnn_predicts_real_generated_images(label):
    with Image.open(SAMPLES[label]) as image:
        result = predict_image(image)
    assert result['prediction'] == label
    assert result['confidence'] > 90
    assert abs(sum(result['probabilities'].values()) - 100) < 0.05
    assert result['image_size'] == '8x8'


def test_cnn_preprocessing_is_grayscale_invariant():
    # Training images are single-channel; RGB copies must give identical scores.
    with Image.open(SAMPLES['Attack']) as image:
        gray = predict_image(image)
        rgb = predict_image(image.convert('RGB'))
    assert gray['probabilities'] == rgb['probabilities']


def test_cnn_rejects_wrong_size():
    with pytest.raises(ValueError):
        predict_image(Image.new('L', (16, 16)))


# ---------------------------------------------------------------- API

@pytest.fixture(scope='module')
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous


@pytest.fixture(scope='module')
def headers(client):
    creds = {'username': 'image_analyst', 'password': 'Image-detection-test-pw!'}
    assert client.post('/api/v1/auth/register', json={**creds, 'role': 'analyst'}).status_code == 200
    token = client.post('/api/v1/auth/login', json=creds).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def upload(client, headers, data, name='sample.png', content_type='image/png'):
    return client.post('/api/v1/image-detection/predict', headers=headers, files={'file': (name, data, content_type)})


def test_image_api_requires_authentication(client):
    assert upload(client, {}, SAMPLES['Attack'].read_bytes()).status_code == 401


@pytest.mark.parametrize('label', ['Attack', 'Benign'])
def test_image_api_predicts(client, headers, label):
    r = upload(client, headers, SAMPLES[label].read_bytes())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['prediction'] == label and body['model'] == 'SmallCNN'
    assert set(body['probabilities']) == {'Attack', 'Benign'}


def test_image_api_accepts_jpeg(client, headers):
    with Image.open(SAMPLES['Benign']) as image:
        data = png_bytes(image.convert('L'), 'JPEG')
    r = upload(client, headers, data, 'sample.jpg', 'image/jpeg')
    assert r.status_code == 200, r.text


def test_image_api_validation(client, headers):
    assert upload(client, headers, b'hello', 'a.txt', 'text/plain').status_code == 415
    assert upload(client, headers, b'not really a png').status_code == 400
    assert upload(client, headers, png_bytes(Image.new('L', (32, 32)))).status_code == 422
    assert upload(client, headers, b'0' * (2 * 1024 * 1024 + 10)).status_code == 413


def test_image_prediction_is_audited(client, headers):
    upload(client, headers, SAMPLES['Attack'].read_bytes())
    entries = client.get('/api/v1/audit', headers=headers).json()
    items = entries['items'] if isinstance(entries, dict) else entries
    assert any(e.get('action') == 'image.predict' for e in items)


def test_existing_routes_still_registered():
    paths = {route.path for route in app.routes}
    for path in ['/health', '/api/v1/dashboard', '/api/v1/devices', '/api/v1/research/dataset-predict/{record_index}',
                 '/api/v1/simulations/{scenario}', '/api/v1/image-detection/predict']:
        assert path in paths, path
