import getpass, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password
Base.metadata.create_all(bind=engine)
db=SessionLocal()
username=input('Administrator username [admin]: ').strip() or 'admin'
if db.query(User).filter_by(username=username).first(): print('User already exists.'); raise SystemExit(1)
password=getpass.getpass('Choose administrator password (10+ characters): ')
if len(password)<10: raise SystemExit('Password must be at least 10 characters.')
db.add(User(username=username,password_hash=hash_password(password),role='administrator')); db.commit(); print(f'Created administrator: {username}')
