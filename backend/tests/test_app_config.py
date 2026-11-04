"""Regression tests for the app-level configuration consolidated during integration."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient

from app.main import DEFAULT_SETTINGS, app

client = TestClient(app)


def test_single_cors_middleware():
    assert sum('CORS' in m.cls.__name__ for m in app.user_middleware) == 1


@pytest.mark.parametrize('origin', ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175', 'http://127.0.0.1:5173'])
def test_cors_allows_dev_ports(origin):
    if os.getenv('FRONTEND_ORIGINS'):
        pytest.skip('FRONTEND_ORIGINS overrides the default origins')
    r = client.options('/health', headers={'Origin': origin, 'Access-Control-Request-Method': 'GET'})
    assert r.headers.get('access-control-allow-origin') == origin


def test_cors_rejects_unknown_origin():
    r = client.options('/health', headers={'Origin': 'http://evil.example', 'Access-Control-Request-Method': 'GET'})
    assert 'access-control-allow-origin' not in r.headers


def test_default_settings_unchanged():
    assert DEFAULT_SETTINGS == {
        'risk_weights': {'authentication': 25, 'behavior': 20, 'communication': 20, 'credentials': 15, 'firmware': 20},
        'communication': {'latency_ms': 120, 'jitter_ms': 35, 'packet_loss_pct': 5, 'reconnects': 8},
        'credentials': {'failed_attempts': 5, 'window_minutes': 10},
        'minimum_firmware_version': '1.0.0',
        'low_coverage_alert_pct': 40,
        'ml': {'contamination': 0.05, 'seed': 42},
    }
    assert sum(DEFAULT_SETTINGS['risk_weights'].values()) == 100


def test_no_duplicate_routes():
    routes = [(tuple(sorted(r.methods)), r.path) for r in app.routes if hasattr(r, 'methods')]
    assert len(routes) == len(set(routes))
    paths = {p for _, p in routes}
    assert '/api/v1/image-detection/predict' in paths
    assert '/api/v1/analysis/network-traffic' in paths
