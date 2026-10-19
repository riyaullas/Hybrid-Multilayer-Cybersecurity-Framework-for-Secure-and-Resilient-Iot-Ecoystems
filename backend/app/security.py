import os, json, time, base64, hashlib, hmac
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

JWT_SECRET = os.getenv('JWT_SECRET', 'development-only-secret-change-me')

def hash_password(password: str) -> str:
    salt=os.urandom(16); digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
    return 'pbkdf2_sha256$310000$'+base64.urlsafe_b64encode(salt).decode()+'$'+base64.urlsafe_b64encode(digest).decode()
def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, expected=stored.split('$'); got=hashlib.pbkdf2_hmac('sha256', password.encode(), base64.urlsafe_b64decode(salt), int(rounds))
        return hmac.compare_digest(base64.urlsafe_b64encode(got).decode(), expected)
    except Exception: return False

def b64(x: bytes) -> str: return base64.urlsafe_b64encode(x).rstrip(b'=').decode()
def create_token(username: str, role: str, minutes: int=60) -> str:
    head=b64(json.dumps({'alg':'HS256','typ':'JWT'}, separators=(',',':')).encode()); payload=b64(json.dumps({'sub':username,'role':role,'exp':int(time.time())+minutes*60},separators=(',',':')).encode())
    msg=f'{head}.{payload}'; sig=b64(hmac.new(JWT_SECRET.encode(),msg.encode(),hashlib.sha256).digest()); return f'{msg}.{sig}'
def decode_token(token: str):
    try:
        h,p,s=token.split('.'); msg=f'{h}.{p}'; expected=b64(hmac.new(JWT_SECRET.encode(),msg.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(s,expected): return None
        data=json.loads(base64.urlsafe_b64decode(p+'='*((4-len(p)%4)%4)))
        if int(data['exp']) < int(time.time()): return None
        return data
    except Exception: return None

def new_device_keypair():
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    priv=private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
    pub=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    fingerprint=hashlib.sha256(pub.encode()).hexdigest()
    return priv,pub,fingerprint

def sign_payload(private_pem: str, payload: str) -> str:
    key=serialization.load_pem_private_key(private_pem.encode(),password=None)
    return base64.b64encode(key.sign(payload.encode(),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())).decode()
def verify_signature(public_pem: str, payload: str, signature: str) -> bool:
    try:
        key=serialization.load_pem_public_key(public_pem.encode())
        key.verify(base64.b64decode(signature),payload.encode(),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256()); return True
    except Exception: return False
