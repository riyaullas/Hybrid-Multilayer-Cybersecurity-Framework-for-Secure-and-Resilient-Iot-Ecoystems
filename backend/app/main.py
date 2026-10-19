import os, json, hashlib, secrets, time, re
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from .database import Base, engine, get_db
from .models import User, Device, Event, Incident, Challenge, Firmware, Audit, AppSetting
from .security import hash_password, verify_password, create_token, decode_token, new_device_keypair, sign_payload, verify_signature
from .ml_service import infer, evaluate, FEATURES
from .network_detection import predict_network_traffic

Base.metadata.create_all(bind=engine)
app=FastAPI(title='MedSecure Sentinel API', version='1.0.0', description='Synthetic healthcare IoT cybersecurity research prototype. All generated activity is simulated.')
origins=os.getenv('FRONTEND_ORIGINS','http://localhost:5173').split(',')
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
KEY_DIR=os.path.join(os.path.dirname(__file__),'..','device_keys'); os.makedirs(KEY_DIR,exist_ok=True)
DEFAULT_SETTINGS={'risk_weights':{'authentication':25,'behavior':20,'communication':20,'credentials':15,'firmware':20},'communication':{'latency_ms':120,'jitter_ms':35,'packet_loss_pct':5,'reconnects':8},'credentials':{'failed_attempts':5,'window_minutes':10},'minimum_firmware_version':'1.0.0','low_coverage_alert_pct':40,'ml':{'contamination':0.05,'seed':42}}

class RegisterIn(BaseModel): username:str=Field(min_length=3,max_length=80); password:str=Field(min_length=10,max_length=128); role:str='analyst'
class LoginIn(BaseModel): username:str; password:str
class DeviceIn(BaseModel): device_id:str=Field(min_length=3,max_length=80); name:str; device_type:str; manufacturer:str='Synthetic Vendor'; firmware_version:str='1.0.0'; ip_address:str='192.0.2.10'; location:str='Simulated Ward A'
class VerifyIn(BaseModel): signature:str
class InferIn(BaseModel): sample:dict[str,float]
class IncidentUpdate(BaseModel): status:Optional[str]=None; assigned_to:Optional[str]=None; resolution_notes:Optional[str]=None
class SettingIn(BaseModel): value:dict
class ScenarioIn(BaseModel): device_id:Optional[str]=None; seed:int=42


def audit(db, actor, action, resource='', outcome='success', metadata=None):
    db.add(Audit(actor=actor,action=action,resource=resource,outcome=outcome,metadata_json=metadata or {}))
def event(db, device_id, category, severity, title, description='', evidence=None):
    e=Event(device_id=device_id,category=category,severity=severity,title=title,description=description,evidence=evidence or {},simulated=True); db.add(e); db.flush(); return e
def create_incident(db, title, category, severity, device_id, description, evidence):
    inc=Incident(title=title,category=category,severity=severity,device_id=device_id,description=description,evidence=evidence or {}); db.add(inc); db.flush(); return inc

def current_user(authorization: str|None=Header(default=None), db:Session=Depends(get_db)):
    if not authorization or not authorization.lower().startswith('bearer '): raise HTTPException(401,'Authentication required')
    claims=decode_token(authorization.split(' ',1)[1]);
    if not claims: raise HTTPException(401,'Invalid or expired access token')
    user=db.query(User).filter_by(username=claims.get('sub'),active=True).first()
    if not user: raise HTTPException(401,'User not available')
    return user
def admin_user(user:User=Depends(current_user)):
    if user.role!='administrator': raise HTTPException(403,'Administrator role required')
    return user

def device_dict(d):
    return {'device_id':d.device_id,'name':d.name,'device_type':d.device_type,'manufacturer':d.manufacturer,'firmware_version':d.firmware_version,'ip_address':d.ip_address,'location':d.location,'enabled':d.enabled,'quarantined':d.quarantined,'key_fingerprint':d.key_fingerprint,'risk_score':round(d.risk_score,2) if d.risk_score is not None else None,'trust_score':round(d.trust_score,2) if d.trust_score is not None else None,'risk_category':d.risk_category,'created_at':d.created_at,'last_seen':d.last_seen}
def event_dict(e): return {'id':e.id,'device_id':e.device_id,'category':e.category,'severity':e.severity,'title':e.title,'description':e.description,'evidence':e.evidence,'simulated':e.simulated,'created_at':e.created_at}
def incident_dict(i): return {'id':i.id,'title':i.title,'description':i.description,'category':i.category,'severity':i.severity,'device_id':i.device_id,'status':i.status,'evidence':i.evidence,'assigned_to':i.assigned_to,'resolution_notes':i.resolution_notes,'created_at':i.created_at,'updated_at':i.updated_at}
def severity(score): return 'Critical' if score>=75 else 'High' if score>=50 else 'Medium' if score>=25 else 'Low'
def recalc_risk(db, d):
    # Each detector contributes only after evidence exists; unevaluated layers are not treated as safe.
    stored=db.query(AppSetting).filter_by(key='risk_weights').first(); weights=stored.value if stored and stored.value else DEFAULT_SETTINGS['risk_weights']; evidence={}; scores={}
    categories={'authentication':'Authentication','behavior':'Behavioral AI','communication':'Communication','credentials':'Credential misuse','firmware':'Firmware integrity'}
    for key,cat in categories.items():
        es=db.query(Event).filter(Event.device_id==d.device_id,Event.category==cat).order_by(desc(Event.id)).limit(30).all()
        if es:
            risk=max([100 if e.severity=='Critical' else 75 if e.severity=='High' else 40 if e.severity=='Medium' else 5 for e in es[:5]])
            scores[key]=risk; evidence[key]=[{'event_id':e.id,'title':e.title,'severity':e.severity} for e in es[:3]]
    available=sum(weights[k] for k in scores)
    overall=sum(scores[k]*weights[k] for k in scores)/available if available else None
    coverage=available/sum(weights.values())*100
    d.risk_score=round(overall,2) if overall is not None else None; d.trust_score=round(100-overall,2) if overall is not None else None; d.risk_category=severity(overall) if overall is not None else 'Not evaluated'
    db.add(Event(device_id=d.device_id,category='Risk assessment',severity=severity(overall) if overall is not None else 'Info',title='Risk score recalculated',description='Weighted score from evaluated security layers.',evidence={'scores':scores,'weights':weights,'coverage_pct':round(coverage,2),'unevaluated':[k for k in weights if k not in scores]},simulated=True))
    return {'device_id':d.device_id,'risk_score':d.risk_score,'trust_score':d.trust_score,'risk_category':d.risk_category,'layer_scores':scores,'layer_evidence':evidence,'coverage_pct':round(coverage,2),'unevaluated_layers':[k for k in weights if k not in scores],'note':'Prototype risk score, not a calibrated probability of compromise.'}

@app.get('/health')
def health(): return {'status':'ok','service':'MedSecure Sentinel API','mode':'synthetic research prototype'}
@app.get('/ready')
def ready(db:Session=Depends(get_db)): return {'ready':True,'database':'connected','devices':db.query(Device).count()}

@app.post('/api/v1/auth/register')
def register(body:RegisterIn, db:Session=Depends(get_db)):
    if body.role not in ['analyst','administrator']: raise HTTPException(422,'Role must be analyst or administrator')
    if db.query(User).filter_by(username=body.username).first(): raise HTTPException(409,'Username already exists')
    if db.query(User).count() and body.role=='administrator': raise HTTPException(403,'Administrator role can only be assigned by an existing administrator')
    u=User(username=body.username,password_hash=hash_password(body.password),role=body.role); db.add(u); audit(db,body.username,'user.register',body.username); db.commit(); return {'username':u.username,'role':u.role}
@app.post('/api/v1/auth/login')
def login(body:LoginIn, db:Session=Depends(get_db)):
    u=db.query(User).filter_by(username=body.username).first()
    if not u or not verify_password(body.password,u.password_hash) or not u.active:
        audit(db,body.username,'auth.login','', 'failure',{'reason':'invalid credentials'}); db.commit(); raise HTTPException(401,'Invalid username or password')
    u.failed_logins=0; token=create_token(u.username,u.role,int(os.getenv('JWT_MINUTES','60'))); audit(db,u.username,'auth.login',u.username); db.commit()
    return {'access_token':token,'token_type':'bearer','expires_in':int(os.getenv('JWT_MINUTES','60'))*60,'user':{'username':u.username,'role':u.role}}
@app.get('/api/v1/auth/me')
def me(user:User=Depends(current_user)): return {'username':user.username,'role':user.role}

@app.get('/api/v1/dashboard')
def dashboard(db:Session=Depends(get_db), user:User=Depends(current_user)):
    devices=db.query(Device).all(); events=db.query(Event).order_by(desc(Event.id)).limit(12).all(); incidents=db.query(Incident).filter(Incident.status!='Resolved').all()
    cat={}
    for e in db.query(Event).all(): cat[e.category]=cat.get(e.category,0)+1
    return {'synthetic':True,'total_devices':len(devices),'low_risk':sum(d.risk_category=='Low' for d in devices),'attention':sum(d.risk_category in ['Medium','High'] for d in devices),'high_critical':sum(d.risk_category in ['High','Critical'] for d in devices),'authentication_failures':db.query(Event).filter(Event.category=='Authentication',Event.severity.in_(['High','Critical'])).count(),'suspicious_communication':db.query(Event).filter(Event.category=='Communication').count(),'behavioral_anomalies':db.query(Event).filter(Event.category=='Behavioral AI').count(),'firmware_failures':db.query(Event).filter(Event.category=='Firmware integrity',Event.severity.in_(['High','Critical'])).count(),'open_incidents':len(incidents),'events_by_category':cat,'risk_distribution':{s:sum(d.risk_category==s for d in devices) for s in ['Low','Medium','High','Critical']},'devices':[device_dict(d) for d in devices],'recent_events':[event_dict(e) for e in events],'recent_incidents':[incident_dict(i) for i in incidents[:5]]}

@app.get('/api/v1/devices')
def list_devices(search:str='', risk:str='', db:Session=Depends(get_db), user:User=Depends(current_user)):
    q=db.query(Device)
    if search: q=q.filter((Device.name.contains(search))|(Device.device_id.contains(search))|(Device.device_type.contains(search)))
    if risk: q=q.filter(Device.risk_category==risk)
    return {'items':[device_dict(d) for d in q.order_by(Device.device_id).all()],'total':q.count()}
@app.post('/api/v1/devices')
def add_device(body:DeviceIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if user.role!='administrator': raise HTTPException(403,'Administrator role required')
    if db.query(Device).filter_by(device_id=body.device_id).first(): raise HTTPException(409,'Device ID already exists')
    private,pub,fp=new_device_keypair(); d=Device(**body.model_dump(),public_key_pem=pub,key_fingerprint=fp); db.add(d)
    with open(os.path.join(KEY_DIR,body.device_id+'.pem'),'w') as f: f.write(private)
    os.chmod(os.path.join(KEY_DIR,body.device_id+'.pem'),0o600)
    audit(db,user.username,'device.register',body.device_id,metadata={'key_fingerprint':fp}); db.commit(); return device_dict(d)
@app.get('/api/v1/devices/{device_id}')
def get_device(device_id:str, db:Session=Depends(get_db), user:User=Depends(current_user)):
    d=db.query(Device).filter_by(device_id=device_id).first()
    if not d: raise HTTPException(404,'Device not found')
    return {**device_dict(d),'events':[event_dict(e) for e in db.query(Event).filter_by(device_id=device_id).order_by(desc(Event.id)).limit(50).all()]}
@app.patch('/api/v1/devices/{device_id}/state')
def device_state(device_id:str, enabled:Optional[bool]=None, quarantined:Optional[bool]=None, db:Session=Depends(get_db), user:User=Depends(current_user)):
    if user.role!='administrator': raise HTTPException(403,'Administrator role required')
    d=db.query(Device).filter_by(device_id=device_id).first()
    if not d: raise HTTPException(404,'Device not found')
    if enabled is not None: d.enabled=enabled
    if quarantined is not None: d.quarantined=quarantined
    audit(db,user.username,'device.state_change',device_id,metadata={'enabled':d.enabled,'quarantined':d.quarantined}); db.commit(); return device_dict(d)

@app.post('/api/v1/authentication/{device_id}/challenge')
def challenge(device_id:str, db:Session=Depends(get_db), user:User=Depends(current_user)):
    d=db.query(Device).filter_by(device_id=device_id).first()
    if not d or not d.enabled or d.quarantined: raise HTTPException(404,'Enabled, non-quarantined device not found')
    nonce=secrets.token_urlsafe(32); exp=datetime.now(timezone.utc)+timedelta(minutes=2); payload=json.dumps({'device_id':device_id,'nonce':nonce,'purpose':'device-authentication','expires_at':exp.isoformat()},sort_keys=True,separators=(',',':'))
    c=Challenge(nonce=nonce,device_id=device_id,payload=payload,expires_at=exp); db.add(c); audit(db,user.username,'auth.challenge.create',device_id); db.commit(); return {'nonce':nonce,'payload':payload,'expires_at':exp,'fingerprint':d.key_fingerprint}
@app.post('/api/v1/authentication/{device_id}/simulate-sign')
def simulate_sign(device_id:str, nonce:str, db:Session=Depends(get_db), user:User=Depends(current_user)):
    c=db.query(Challenge).filter_by(device_id=device_id,nonce=nonce).first()
    if not c or c.consumed: raise HTTPException(400,'Challenge missing or already consumed')
    keypath=os.path.join(KEY_DIR,device_id+'.pem')
    if not os.path.exists(keypath): raise HTTPException(400,'Local simulation private key unavailable')
    signature=sign_payload(open(keypath).read(),c.payload); return {'signature':signature,'warning':'Development-only simulated device signing; private key is kept server-side.'}
@app.post('/api/v1/authentication/{device_id}/verify')
def verify_auth(device_id:str, body:VerifyIn, nonce:str=Query(...), db:Session=Depends(get_db), user:User=Depends(current_user)):
    c=db.query(Challenge).filter_by(device_id=device_id,nonce=nonce).first(); d=db.query(Device).filter_by(device_id=device_id).first()
    if not c or not d: raise HTTPException(404,'Challenge or device not found')
    if c.consumed: event(db,device_id,'Authentication','High','Replay attempt rejected','Challenge was already consumed.'); audit(db,user.username,'auth.verify',device_id,'failure',{'reason':'replay'}); db.commit(); raise HTTPException(409,'Challenge already consumed (replay rejected)')
    c.consumed=True; exp=c.expires_at
    if exp.tzinfo is None: exp=exp.replace(tzinfo=timezone.utc)
    valid=exp>datetime.now(timezone.utc) and verify_signature(d.public_key_pem or '',c.payload,body.signature)
    if valid: event(db,device_id,'Authentication','Info','Device signature verified','Valid RSA-PSS/SHA-256 signature.',{'fingerprint':d.key_fingerprint}); d.last_seen=datetime.now(timezone.utc)
    else: event(db,device_id,'Authentication','High','Device signature rejected','Invalid, malformed, or expired signature.',{'challenge_expired':exp<=datetime.now(timezone.utc)}); create_incident(db,'Invalid device signature','Authentication','High',device_id,'Device authentication verification failed.',{'fingerprint':d.key_fingerprint})
    audit(db,user.username,'auth.verify',device_id,'success' if valid else 'failure'); db.commit(); return {'verified':valid,'status':'Verified' if valid else 'Rejected','algorithm':'RSA-PSS with SHA-256','fingerprint':d.key_fingerprint}

@app.post('/api/v1/analysis/behavior')
def behavior(body:InferIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    try: result=infer(body.sample)
    except (ValueError,TypeError) as e: raise HTTPException(422,str(e))
    did=body.sample.get('device_id'); d=db.query(Device).filter_by(device_id=did).first() if isinstance(did,str) else None
    sev='High' if result['classification']=='Anomalous' else 'Info'; event(db,d.device_id if d else None,'Behavioral AI',sev,'Behavioral anomaly '+result['classification'].lower(), 'Isolation Forest synthetic telemetry inference.',result)
    if d and result['classification']=='Anomalous': create_incident(db,'Abnormal device behavior','Behavioral AI','High',d.device_id,'Isolation Forest marked synthetic telemetry as anomalous.',result); recalc_risk(db,d)
    audit(db,user.username,'behavior.analyze',d.device_id if d else 'batch',metadata={'classification':result['classification']}); db.commit(); return result
@app.post('/api/v1/analysis/behavior/evaluate')



class NetworkTrafficIn(BaseModel):
    sample: dict[str, float]


@app.post("/api/v1/analysis/network-traffic")
def network_traffic_analysis(
    body: NetworkTrafficIn,
    user: User = Depends(current_user),
):
    try:
        return predict_network_traffic(body.sample)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

def behavior_eval(user:User=Depends(current_user)): return evaluate()

@app.post('/api/v1/simulations/{scenario}')
def run_scenario(scenario:str, body:ScenarioIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    d=db.query(Device).filter_by(device_id=body.device_id).first() if body.device_id else db.query(Device).first()
    if not d: raise HTTPException(400,'Create or seed a device first')
    before={'risk_score':d.risk_score,'trust_score':d.trust_score,'risk_category':d.risk_category}; outputs=[]
    if scenario=='normal':
        event(db,d.device_id,'Authentication','Info','Normal authentication succeeded','Synthetic normal scenario.',{'signature':'valid simulated RSA-PSS'}); event(db,d.device_id,'Behavioral AI','Info','Normal telemetry observed','Synthetic telemetry within baseline.',{'packet_rate':40,'response_ms':35}); event(db,d.device_id,'Communication','Info','Communication baseline normal','No configured communication rule exceeded.',{'latency_ms':35,'jitter_ms':4,'packet_loss_pct':0.2}); event(db,d.device_id,'Firmware integrity','Info','Firmware integrity verified','Synthetic trusted digest matched.',{'hash_match':True,'version':d.firmware_version}); outputs.append('Normal synthetic evidence recorded')
    elif scenario in ['invalid-signature','credential-misuse']:
        cat='Authentication' if scenario=='invalid-signature' else 'Credential misuse'; title='Invalid device signature rejected' if scenario=='invalid-signature' else 'Credential misuse threshold exceeded'; ev={'failed_attempts':7,'window_minutes':5,'rule':'failed_attempts >= 5'}
        event(db,d.device_id,cat,'High',title,'Controlled simulated security scenario.',ev); create_incident(db,title,cat,'High',d.device_id,'Investigation required; this is simulated evidence.',ev); outputs.append('High-severity event and incident created')
    elif scenario=='abnormal-behavior':
        sample={'packet_rate':130,'response_ms':190,'cpu_pct':92,'memory_pct':93,'failed_requests':9,'connection_frequency':14,'bytes_sent':95000,'session_seconds':40,'reconnections':6,'error_frequency':8}
        result=infer(sample); event(db,d.device_id,'Behavioral AI','High','Abnormal synthetic telemetry detected','Isolation Forest inference.',result); create_incident(db,'Abnormal device behavior','Behavioral AI','High',d.device_id,'Isolation Forest anomaly from synthetic sample.',result); outputs.append(result)
    elif scenario=='suspicious-communication':
        ev={'latency_ms':260,'jitter_ms':75,'packet_loss_pct':12,'reconnections':11,'thresholds':DEFAULT_SETTINGS['communication'],'indicators':['latency spike','high jitter','packet loss','reconnection burst']}; event(db,d.device_id,'Communication','High','Suspicious communication indicators','MITM-like indicators; not proof of interception.',ev); create_incident(db,'Suspicious communication pattern','Communication','High',d.device_id,'Multiple simulated communication indicators exceeded thresholds.',ev); outputs.append(ev)
    elif scenario in ['tampered-firmware','firmware-downgrade']:
        ver='0.9.0' if scenario=='firmware-downgrade' else d.firmware_version; ev={'version':ver,'minimum_version':DEFAULT_SETTINGS['minimum_firmware_version'],'hash_match':False if scenario=='tampered-firmware' else None,'rule':'SHA-256 mismatch' if scenario=='tampered-firmware' else 'version below minimum'}
        title='Firmware hash mismatch' if scenario=='tampered-firmware' else 'Firmware downgrade blocked'; event(db,d.device_id,'Firmware integrity','Critical',title,'Synthetic firmware policy violation.',ev); create_incident(db,title,'Firmware integrity','Critical',d.device_id,'Firmware policy violation in controlled simulation.',ev); outputs.append(ev)
    elif scenario=='combined':
        for cat,title,sev,ev in [('Authentication','Invalid signature', 'High',{'valid':False}),('Behavioral AI','Anomalous telemetry','High',{'packet_rate':130,'cpu_pct':92}),('Communication','Suspicious communication','High',{'latency_ms':260,'jitter_ms':75}),('Credential misuse','Repeated failed authentication','High',{'failed_attempts':7}),('Firmware integrity','Firmware integrity mismatch','Critical',{'hash_match':False})]:
            event(db,d.device_id,cat,sev,title,'Combined simulated scenario.',ev)
        create_incident(db,'Combined multilayer security incident','Multilayer','Critical',d.device_id,'Multiple synthetic security layers generated alerts.',{'layers':['authentication','behavior','communication','credentials','firmware']}); outputs.append('Five layers recorded and consolidated incident created')
    else: raise HTTPException(404,'Unknown scenario. Use normal, invalid-signature, abnormal-behavior, suspicious-communication, credential-misuse, tampered-firmware, firmware-downgrade, combined.')
    risk=recalc_risk(db,d); audit(db,user.username,'simulation.run',scenario,metadata={'device_id':d.device_id,'simulated':True}); db.commit()
    return {'scenario':scenario,'simulated':True,'device_id':d.device_id,'before':before,'after':{'risk_score':d.risk_score,'trust_score':d.trust_score,'risk_category':d.risk_category},'risk_assessment':risk,'results':outputs,'events':[event_dict(e) for e in db.query(Event).filter_by(device_id=d.device_id).order_by(desc(Event.id)).limit(10).all()],'incidents':[incident_dict(i) for i in db.query(Incident).filter_by(device_id=d.device_id).order_by(desc(Incident.id)).limit(5).all()]}

@app.post('/api/v1/risk/{device_id}/recalculate')
def risk(device_id:str, db:Session=Depends(get_db), user:User=Depends(current_user)):
    d=db.query(Device).filter_by(device_id=device_id).first()
    if not d: raise HTTPException(404,'Device not found')
    result=recalc_risk(db,d); audit(db,user.username,'risk.recalculate',device_id); db.commit(); return result
@app.get('/api/v1/incidents')
def incidents(status:str='', db:Session=Depends(get_db), user:User=Depends(current_user)):
    q=db.query(Incident)
    if status: q=q.filter(Incident.status==status)
    return {'items':[incident_dict(i) for i in q.order_by(desc(Incident.created_at)).all()]}
@app.patch('/api/v1/incidents/{incident_id}')
def update_incident(incident_id:int, body:IncidentUpdate, db:Session=Depends(get_db), user:User=Depends(current_user)):
    i=db.query(Incident).filter_by(id=incident_id).first()
    if not i: raise HTTPException(404,'Incident not found')
    if body.status and body.status not in ['Open','Acknowledged','Investigating','Resolved']: raise HTTPException(422,'Invalid incident status')
    previous=i.status
    for k,v in body.model_dump(exclude_none=True).items(): setattr(i,k,v)
    audit(db,user.username,'incident.status_change',str(i.id),metadata={'from':previous,'to':i.status}); db.commit(); return incident_dict(i)
@app.get('/api/v1/events')
def events(category:str='', db:Session=Depends(get_db), user:User=Depends(current_user)):
    q=db.query(Event)
    if category: q=q.filter(Event.category==category)
    return {'items':[event_dict(e) for e in q.order_by(desc(Event.id)).limit(500).all()]}
@app.get('/api/v1/topology')
def topology(db:Session=Depends(get_db), user:User=Depends(current_user)):
    devices=db.query(Device).all(); nodes=[{'id':d.device_id,'type':'gateway' if 'gateway' in d.device_type.lower() else 'device','label':d.name,'device':device_dict(d)} for d in devices]
    edges=[]; gateway=next((d for d in devices if 'gateway' in d.device_type.lower()),None)
    if gateway:
        for d in devices:
            if d.device_id != gateway.device_id: edges.append({'id':f'{gateway.device_id}-{d.device_id}','source':gateway.device_id,'target':d.device_id,'suspicious':d.risk_category in ['High','Critical']})
    return {'synthetic':True,'nodes':nodes,'edges':edges}
@app.get('/api/v1/audit')
def audit_logs(db:Session=Depends(get_db), user:User=Depends(current_user)):
    return {'items':[{'id':a.id,'actor':a.actor,'action':a.action,'resource':a.resource,'outcome':a.outcome,'metadata':a.metadata_json,'created_at':a.created_at} for a in db.query(Audit).order_by(desc(Audit.id)).limit(500).all()]}
@app.get('/api/v1/settings')
def settings(db:Session=Depends(get_db), user:User=Depends(current_user)):
    stored={s.key:s.value for s in db.query(AppSetting).all()}; return {**DEFAULT_SETTINGS,**stored}
@app.put('/api/v1/settings/{key}')
def update_setting(key:str, body:SettingIn, db:Session=Depends(get_db), user:User=Depends(admin_user)):
    if key not in DEFAULT_SETTINGS: raise HTTPException(404,'Unknown setting key')
    if key=='risk_weights':
        vals=body.value
        if set(vals)!=set(DEFAULT_SETTINGS['risk_weights']) or any(not isinstance(v,(int,float)) or v<0 for v in vals.values()) or abs(sum(vals.values())-100)>0.001: raise HTTPException(422,'Risk weights must include all five layers and total 100')
    row=db.query(AppSetting).filter_by(key=key).first()
    if row: row.value=body.value
    else: db.add(AppSetting(key=key,value=body.value))
    audit(db,user.username,'settings.update',key,metadata=body.value); db.commit(); return {'key':key,'value':body.value}
@app.get('/api/v1/research/evaluation')
def research(user:User=Depends(current_user)): return evaluate()
@app.get('/api/v1/research/features')
def research_features(user:User=Depends(current_user)): return {'features':FEATURES,'synthetic':True}
@app.get('/api/v1/export/devices')
def export_devices(db:Session=Depends(get_db), user:User=Depends(current_user)):
    import csv,io
    from fastapi.responses import StreamingResponse
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=['device_id','name','device_type','firmware_version','ip_address','location','risk_score','trust_score','risk_category']); w.writeheader()
    for d in db.query(Device).all(): w.writerow({k:device_dict(d).get(k) for k in w.fieldnames})
    from io import BytesIO
    return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="medsecure-devices.csv"'})
@app.post('/api/v1/seed')
def seed(db:Session=Depends(get_db), user:User=Depends(admin_user)):
    if db.query(Device).count(): return {'message':'Sample devices already exist','count':db.query(Device).count()}
    samples=[('MON-001','Bedside Monitor 01','Patient monitor','192.0.2.11'),('WRB-002','Wearable Sensor 02','Wearable sensor','192.0.2.12'),('GW-001','Monitoring Gateway','Remote patient-monitoring gateway','192.0.2.20'),('MED-003','Smart Infusion Unit 03','Smart medical equipment','192.0.2.13'),('ENV-004','Room Environment Sensor','Environmental monitoring sensor','192.0.2.14')]
    for did,name,typ,ip in samples:
        priv,pub,fp=new_device_keypair(); d=Device(device_id=did,name=name,device_type=typ,ip_address=ip,public_key_pem=pub,key_fingerprint=fp); db.add(d); db.flush()
        with open(os.path.join(KEY_DIR,did+'.pem'),'w') as f: f.write(priv)
        os.chmod(os.path.join(KEY_DIR,did+'.pem'),0o600)
    db.commit(); audit(db,user.username,'demo.seed','devices',metadata={'count':len(samples)}); db.commit(); return {'message':'Synthetic devices initialized','count':len(samples),'synthetic':True}
