"""Tests for the CICIoMT2024 Random Forest network-traffic module and its API route."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.network_detection import FEATURES, predict_network_traffic

# Two real rows from the CICIoMT2024 binary test split (ARP spoofing attack, benign).
SAMPLES = json.loads((Path(__file__).parent / 'fixtures' / 'network_flow_samples.json').read_text())
TEST_CSV = Path(os.environ.get('MEDSECURE_CICIOMT_TEST_CSV', 'D:/MedSecure-ML/data/binary_evaluation/test.csv'))


# ---------------------------------------------------------------- service

def test_model_feature_contract():
    assert len(FEATURES) == 45
    assert set(SAMPLES['Attack']['features']) == set(FEATURES)


@pytest.mark.parametrize('label', ['Attack', 'Benign'])
def test_random_forest_predicts_real_flows(label):
    result = predict_network_traffic(SAMPLES[label]['features'])
    assert result['classification'] == label
    assert result['probabilities'][label] >= 0.9
    assert result['feature_count'] == 45


def test_random_forest_rejects_bad_input():
    sample = dict(SAMPLES['Benign']['features'])
    sample.pop('Rate')
    with pytest.raises(ValueError, match='Missing required'):
        predict_network_traffic(sample)
    with pytest.raises(ValueError):
        predict_network_traffic({**SAMPLES['Benign']['features'], 'Rate': float('inf')})


@pytest.mark.skipif(not TEST_CSV.exists(), reason='CICIoMT2024 test split not available on this machine')
def test_random_forest_reproduces_recorded_test_accuracy():
    import numpy as np
    import pandas as pd
    from app.network_detection import imputer, model
    df = pd.read_csv(TEST_CSV)
    y = df['label'].astype(str).str.strip()
    keep = y.isin(['Attack', 'Benign'])
    X = df.loc[keep, FEATURES].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)
    pred = model.predict(imputer.transform(X))
    # Recorded in ml_image_detection/reports/tabular/random_forest_metrics.json: 0.9866858626502762 on 81,267 rows.
    assert len(pred) == 81267
    assert abs(float((pred == y[keep].to_numpy()).mean()) - 0.9866858626502762) < 1e-12


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
    creds = {'username': 'network_analyst', 'password': 'Network-detection-test-pw!'}
    assert client.post('/api/v1/auth/register', json={**creds, 'role': 'analyst'}).status_code == 200
    token = client.post('/api/v1/auth/login', json=creds).json()['access_token']
    return {'Authorization': f'Bearer {token}'}


URL = '/api/v1/analysis/network-traffic'


def test_network_api_requires_authentication(client):
    assert client.post(URL, json={'sample': SAMPLES['Attack']['features']}).status_code == 401


@pytest.mark.parametrize('label', ['Attack', 'Benign'])
def test_network_api_predicts(client, headers, label):
    r = client.post(URL, headers=headers, json={'sample': SAMPLES[label]['features']})
    assert r.status_code == 200, r.text
    assert r.json()['classification'] == label
    assert r.json()['model'] == 'RandomForest-CICIoMT2024'


def test_network_api_validation(client, headers):
    partial = dict(SAMPLES['Benign']['features'])
    partial.pop('Rate')
    assert client.post(URL, headers=headers, json={'sample': partial}).status_code == 422
    assert client.post(URL, headers=headers, json={'sample': {**partial, 'Rate': 'abc'}}).status_code == 422


def test_network_prediction_is_audited(client, headers):
    client.post(URL, headers=headers, json={'sample': SAMPLES['Attack']['features']})
    entries = client.get('/api/v1/audit', headers=headers).json()
    items = entries['items'] if isinstance(entries, dict) else entries
    assert any(e.get('action') == 'network.analyze' for e in items)
