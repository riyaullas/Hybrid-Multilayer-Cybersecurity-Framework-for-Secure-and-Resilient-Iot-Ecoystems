# User Guide

1. Start backend and frontend following the root README.
2. Create a local administrator with `python scripts/create_admin.py` in the backend directory.
3. Sign in to MedSecure Sentinel.
4. Seed sample devices with the authenticated `POST /api/v1/seed` endpoint, or register one in Device Inventory.
5. Open Overview to see persisted dashboard aggregates.
6. Open Device Authentication to generate a challenge, use the local simulation signer, and verify. Change one character of the signature to demonstrate rejection; challenge consumption means create a new challenge for each verification attempt.
7. Use Guided Demo Lab to run any scenario. Each response includes before/after risk and evidence.
8. Review Security Incidents and update status through the Actions selector.
9. Open Behavioral AI Lab to submit numeric telemetry and review model output and unusual-feature explanations.
10. Open Research Evaluation to review confusion-matrix metrics and print/save the page.
11. Use Audit Logs to review application actions.

All sample data is synthetic. Do not enter real patient information or production secrets.
