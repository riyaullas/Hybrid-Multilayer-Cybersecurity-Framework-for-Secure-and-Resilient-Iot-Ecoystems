# API Documentation (overview)

The interactive OpenAPI schema is available at `/docs` while the backend is running. API paths below are relative to `http://localhost:8000`.

Most `/api/v1` endpoints require `Authorization: Bearer <access_token>`.

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/health` | Public | Liveness check |
| GET | `/ready` | Public | Database readiness |
| POST | `/api/v1/auth/register` | Public/local | Create first local account; later registration is analyst-only |
| POST | `/api/v1/auth/login` | Public | Verify credentials and issue JWT |
| GET | `/api/v1/auth/me` | Authenticated | Current user |
| GET | `/api/v1/dashboard` | Authenticated | Persisted aggregates and recent records |
| GET/POST | `/api/v1/devices` | Authenticated / administrator for create | List/filter and register devices |
| GET | `/api/v1/devices/{device_id}` | Authenticated | Device and recent event details |
| POST | `/api/v1/authentication/{device_id}/challenge` | Authenticated | Create expiring challenge |
| POST | `/api/v1/authentication/{device_id}/simulate-sign?nonce=...` | Authenticated | Local educational signature simulation |
| POST | `/api/v1/authentication/{device_id}/verify?nonce=...` | Authenticated | Consume and verify challenge |
| POST | `/api/v1/analysis/behavior` | Authenticated | Analyze one telemetry sample |
| POST | `/api/v1/analysis/behavior/evaluate` | Authenticated | Run held-out synthetic benchmark |
| POST | `/api/v1/simulations/{scenario}` | Authenticated | Run one of eight controlled scenarios |
| POST | `/api/v1/risk/{device_id}/recalculate` | Authenticated | Recompute risk and coverage |
| GET/PATCH | `/api/v1/incidents` and `/api/v1/incidents/{id}` | Authenticated | Incident list and status transition |
| GET | `/api/v1/topology` | Authenticated | Synthetic topology graph |
| GET | `/api/v1/audit` | Authenticated | Recent audit rows |
| GET | `/api/v1/settings` | Authenticated | Configuration values |
| PUT | `/api/v1/settings/{key}` | Administrator | Update supported setting |
| GET | `/api/v1/research/evaluation` | Authenticated | Reproducible synthetic metrics |
| GET | `/api/v1/export/devices` | Authenticated | CSV inventory download |
| POST | `/api/v1/seed` | Administrator | Seed sample devices once |

## Example: login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"YOUR_LOCAL_PASSWORD"}'
```

## Example: run combined scenario

```bash
curl -X POST http://localhost:8000/api/v1/simulations/combined \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' -d '{"seed":42}'
```

Scenario names: `normal`, `invalid-signature`, `abnormal-behavior`, `suspicious-communication`, `credential-misuse`, `tampered-firmware`, `firmware-downgrade`, `combined`.

## Common errors

- `401`: missing/invalid/expired token or invalid credentials.
- `403`: insufficient role.
- `404`: unknown resource.
- `409`: duplicate resource or already-consumed challenge.
- `422`: request validation/policy failure.
