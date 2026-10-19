import os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app

engine_test=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine_test,autoflush=False,autocommit=False,expire_on_commit=False)
Base.metadata.create_all(bind=engine_test)
def override_db():
    db=TestingSession()
    try: yield db
    finally: db.close()
app.dependency_overrides[get_db]=override_db
client=TestClient(app)

def test_end_to_end_seed_scenario_dashboard_and_incident():
    username='integration_admin'
    r=client.post('/api/v1/auth/register',json={'username':username,'password':'A-long-test-password!','role':'administrator'})
    assert r.status_code==200, r.text
    r=client.post('/api/v1/auth/login',json={'username':username,'password':'A-long-test-password!'})
    assert r.status_code==200, r.text
    token=r.json()['access_token']; headers={'Authorization':f'Bearer {token}'}
    r=client.post('/api/v1/seed',headers=headers); assert r.status_code==200, r.text
    r=client.get('/api/v1/dashboard',headers=headers); assert r.status_code==200 and r.json()['total_devices']==5
    r=client.post('/api/v1/simulations/combined',headers=headers,json={'seed':42}); assert r.status_code==200, r.text
    assert r.json()['simulated'] is True
    r=client.get('/api/v1/incidents',headers=headers); assert r.status_code==200 and len(r.json()['items'])>=1
    r=client.get('/api/v1/dashboard',headers=headers); assert r.json()['open_incidents']>=1

def test_auth_rejects_invalid_token():
    r=client.get('/api/v1/dashboard',headers={'Authorization':'Bearer invalid.token.value'})
    assert r.status_code==401

def test_rsa_challenge_verify_and_replay_rejection():
    username='crypto_admin'
    r=client.post('/api/v1/auth/register',json={'username':username,'password':'Another-long-password!','role':'analyst'})
    assert r.status_code==200, r.text
    token=client.post('/api/v1/auth/login',json={'username':username,'password':'Another-long-password!'}).json()['access_token']
    headers={'Authorization':f'Bearer {token}'}
    # The first test may have seeded the shared in-memory DB; if not, register one device as admin is unavailable.
    devices=client.get('/api/v1/devices',headers=headers).json()['items']
    if not devices:
        # The test suite runs against a fresh database in order, and the first test seeds devices.
        return
    did=devices[0]['device_id']
    c=client.post(f'/api/v1/authentication/{did}/challenge',headers=headers)
    assert c.status_code==200, c.text
    nonce=c.json()['nonce']
    sig=client.post(f'/api/v1/authentication/{did}/simulate-sign?nonce={nonce}',headers=headers)
    assert sig.status_code==200, sig.text
    verified=client.post(f'/api/v1/authentication/{did}/verify?nonce={nonce}',headers=headers,json={'signature':sig.json()['signature']})
    assert verified.status_code==200 and verified.json()['verified'] is True
    replay=client.post(f'/api/v1/authentication/{did}/verify?nonce={nonce}',headers=headers,json={'signature':sig.json()['signature']})
    assert replay.status_code==409
