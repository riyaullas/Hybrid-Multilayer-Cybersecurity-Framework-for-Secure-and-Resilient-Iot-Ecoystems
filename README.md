# MedSecure Sentinel

**Official project title:** *A Hybrid Multilayer Cybersecurity Framework for Secure and Resilient IoT Ecosystems*  
**Tagline:** Intelligent Security for Resilient IoT Ecosystems

MedSecure Sentinel is a software-only academic research prototype for examining multilayer security controls in a **simulated healthcare IoT environment**. It combines RSA-PSS challenge-response, synthetic telemetry anomaly detection with Isolation Forest, transparent communication indicators, credential-misuse scenarios, firmware digest/version checks, explainable prototype risk scoring, incidents, and audit records.

> **Research and safety boundary:** This is not a clinical system and has not been validated for hospital deployment. Devices, IP addresses, telemetry, and attacks are synthetic. Communication anomalies are not proof of a man-in-the-middle attack. Risk weights are initial assumptions, not calibrated probabilities. No uploaded firmware is executed.

## Architecture

- `frontend/`: React + TypeScript + Vite responsive operations UI.
- `backend/`: FastAPI, SQLAlchemy, SQLite, cryptography, scikit-learn, synthetic scenario APIs.
- `docs/`: architecture, threat model, API overview, research evaluation, and user guide.
- `data/`: sample and generated experiment outputs.

## Requirements

- Python 3.11+ (tested with Python 3.13 in the authoring environment)
- Node.js 20+ and npm
- Internet access for first-time npm/pip dependency installation; runtime scenarios can operate locally after installation.

## Backend setup

Open a terminal in `medsecure-sentinel/backend`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set a long random `JWT_SECRET`. The current application reads environment variables from the process; if you use a `.env` file, export/load its values in your shell or install a dotenv loader and enable it. Defaults are for local development only.

Create a development administrator (the password is entered interactively and is never printed):

```bash
python scripts/create_admin.py
```

Start the API:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- Swagger docs: http://localhost:8000/docs

The SQLite database is created at `backend/medsecure.db` on first startup. For a custom location, set `DATABASE_URL` before starting the API.

## Frontend setup

Open a second terminal in `medsecure-sentinel/frontend`:

```bash
npm install
npm run dev
```

Open http://localhost:5173 and sign in with the administrator credentials you created above. The frontend API default is `http://localhost:8000/api/v1`; override with `VITE_API_URL` if needed.

## First-run demo sequence

1. Sign in as the administrator.
2. Open **Device Inventory** and use the backend seed endpoint to create sample devices (see below), or register a device in the UI.
3. To seed the default set, call the authenticated endpoint `POST /api/v1/seed` with the admin token. Example:

```bash
curl -X POST http://localhost:8000/api/v1/seed -H "Authorization: Bearer YOUR_TOKEN"
```

4. Open **Guided Demo Lab** and execute scenarios A–H.
5. Review changes in **Security Incidents**, **Trust & Risk Engine**, **Audit Logs**, and **Research Evaluation**.
6. Use the authentication page to generate a challenge, simulate local signing, and verify. Modify the signature before verification to demonstrate rejection.

A first registered account is allowed to choose a role when no users exist, so create the administrator only in a trusted local environment. Once a user exists, public registration cannot create another administrator. For a shared or public deployment, disable public registration and implement a controlled administrator provisioning workflow before use.

## Model and research scripts

```bash
cd backend
python scripts/train_model.py
pytest -q
```

The training/evaluation script writes a reproducible JSON summary to `data/generated/synthetic_evaluation.json`. The Isolation Forest is trained on generated normal samples and evaluated against held-out normal plus separately generated abnormal samples. The result measures only the artificial distribution produced by this project.

## API areas

| Prefix | Purpose |
|---|---|
| `/api/v1/auth/*` | Registration, login, current user |
| `/api/v1/dashboard` | Persisted dashboard aggregates |
| `/api/v1/devices` | Device inventory and state |
| `/api/v1/authentication/*` | RSA-PSS challenge-response |
| `/api/v1/analysis/behavior*` | Isolation Forest inference/evaluation |
| `/api/v1/simulations/{scenario}` | Reproducible security scenarios |
| `/api/v1/risk/*` | Explainable risk recalculation |
| `/api/v1/incidents` | Incident status workflow |
| `/api/v1/topology` | Synthetic device graph |
| `/api/v1/research/*` | Synthetic evaluation metrics |
| `/api/v1/audit` | Recent audit entries |
| `/api/v1/settings` | Read prototype configuration |
| `/api/v1/export/devices` | CSV device export |

All API data are authenticated except health/readiness and registration/login. Interactive API docs provide request/response schemas.

## Risk model

Initial layer weights: authentication 25%, behavior 20%, communication 20%, credential misuse 15%, firmware integrity 20%. For each evaluated layer, the latest high-severity evidence among recent events contributes a simple risk value (Info 5, Medium 40, High 75, Critical 100). The aggregate is the weighted mean over **evaluated** layers only; coverage is the sum of evaluated layer weights. Unevaluated layers are reported explicitly, not silently treated as safe. Trust = 100 − risk. This is an illustrative scoring policy, not a validated compromise probability.

## Security notes and limitations

- Passwords use PBKDF2-HMAC-SHA256 with per-password random salt. JWTs are signed HS256 bearer tokens with expiration. Configure a strong secret; use TLS and a hardened identity/session design before deployment.
- Demo device private keys are generated locally and stored in `backend/device_keys/` with restrictive file permissions. The simulated signing endpoint is intentionally educational; it is not a real device trust boundary.
- The database audit trail is append-oriented but is not tamper-proof.
- The prototype's configuration settings page is primarily a read-only view; a subset of backend settings can be updated by administrator APIs. Validate and review any changes.
- This implementation does not include real packet capture, external network scanning, real healthcare telemetry, secure boot, or physical hardware attestation.
- Browser CSV/file upload and a firmware upload UI are not implemented in this first runnable version; digest mismatch and rollback are covered through reproducible backend scenarios.

## Troubleshooting

- **Login fails:** create the admin with `python scripts/create_admin.py`; confirm the backend is running and the browser API URL is correct.
- **API offline indicator:** open `http://localhost:8000/health` and check CORS origins.
- **No devices:** use the authenticated `POST /api/v1/seed` endpoint or register one as admin.
- **Private-key file error:** do not delete `backend/device_keys/` during an authentication demonstration; re-register/reseed devices if the local demo key is missing.
- **Database reset:** stop the backend, back up if needed, remove `backend/medsecure.db` and `backend/device_keys/`, restart the backend, create an administrator, and seed again. This deletes local demo state.

## Suggested lecturer demonstration (5–7 minutes)

1. Explain the five security layers and synthetic-only boundary.
2. Show the device inventory and current risk distribution.
3. Verify a valid RSA-PSS challenge; then demonstrate invalid signature rejection.
4. Run abnormal behavior and suspicious communication scenarios.
5. Run the combined scenario and inspect its incident and evidence.
6. Open research metrics and explain that the benchmark is synthetic, not a real-world performance claim.

## Status

This repository contains a functional academic prototype foundation with authenticated APIs, database persistence, RSA-PSS verification, synthetic Isolation Forest inference/evaluation, scenario generation, incident workflow, risk scoring, topology data, and a responsive UI. It is not a fully production-hardened deployment; consult the limitations above and `docs/` before presenting the implementation scope.
