# Threat Model

## Assets

- User credentials and access tokens.
- Device public-key metadata and local simulation private keys.
- One-time authentication challenges.
- Device configuration and firmware integrity metadata.
- Security events, incident records, risk scores, and audit records.

## Threat scenarios and mitigations

| Threat | Prototype control | Limitation |
|---|---|---|
| Password guessing | PBKDF2 password hashes; bearer JWT expiry | Per-account lockout/rate limiting is not fully implemented |
| Forged device identity | RSA-PSS signature verification | Local simulated signer does not prove hardware identity |
| Replay of a valid challenge | One-time consumed challenge and expiry | Local SQLite concurrency is not a distributed replay store |
| Abnormal telemetry | Isolation Forest + transparent feature deviation explanation | Trained/evaluated on synthetic data only |
| Suspicious network conditions | Configurable statistical indicators | Latency/jitter are not proof of MITM |
| Repeated credential failures | Simulated threshold events and incidents | No production identity-provider integration |
| Firmware tampering | Trusted SHA-256 digest comparison in scenario | Firmware upload and signed manifest UI are not implemented in this version |
| Firmware downgrade | Version-policy scenario and minimum version setting | Version policy is a prototype rule, not secure boot |
| Unauthorized administrative changes | Backend role dependency on sensitive routes; audit rows | Audit database can be modified by a privileged operator |
| Malicious upload | No uploaded firmware is executed | Full firmware upload flow is not included in this version |

## Out of scope

Real patient data, clinical decisions, live network interception, scanning external networks, production hospital deployment, secure boot, hardware roots of trust, cloud key management, tamper-proof logging, and regulatory certification are out of scope.

## Assumptions

The operator runs the application on a trusted local machine, uses synthetic test data, sets a unique JWT secret, protects the `device_keys` directory, and does not expose the development server to untrusted networks.
