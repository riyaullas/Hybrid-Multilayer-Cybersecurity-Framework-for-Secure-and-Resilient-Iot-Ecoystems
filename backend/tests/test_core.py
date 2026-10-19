import os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from app.security import hash_password, verify_password, new_device_keypair, sign_payload, verify_signature, create_token, decode_token
from app.ml_service import infer, evaluate, FEATURES
from app.main import severity

def test_password_hashing():
    h=hash_password('A-long-test-password!'); assert verify_password('A-long-test-password!',h); assert not verify_password('wrong',h)
def test_rsa_signature_and_tamper():
    private,public,_=new_device_keypair(); sig=sign_payload(private,'challenge payload'); assert verify_signature(public,'challenge payload',sig); assert not verify_signature(public,'modified payload',sig)
def test_jwt_roundtrip():
    t=create_token('analyst','analyst'); assert decode_token(t)['sub']=='analyst'; assert decode_token(t+'.x') is None
def test_ml_schema_and_evaluation():
    sample={f:1.0 for f in FEATURES}; result=infer(sample); assert result['classification'] in ['Normal','Anomalous']; assert 'decision_score' in result
    ev=evaluate(); assert ev['test_samples']>0 and 0<=ev['f1']<=1
def test_severity_boundaries():
    assert severity(24)=='Low'; assert severity(25)=='Medium'; assert severity(50)=='High'; assert severity(75)=='Critical'
