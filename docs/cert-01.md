# CERT-01 — Credential Registry & Revocation

## Scope

Skills & Credentials now supports role-scoped credential administration in addition to the existing trainee credential view.

### Trainee
- View issued credentials.
- Download an active certificate PDF.
- Open public verification.

### NCCT Admin / Institute Admin / Trainer
- View credentials within their permitted scope.
- See trainee, course, credential number, status, score and issue date.
- Revoke an issued credential with a recorded reason.

Public verification only validates credentials whose status is `ISSUED`. Revoked credentials no longer validate and active certificate download is blocked for revoked credentials.

## API

- `GET /api/v1/credentials/registry`
- `POST /api/v1/credentials/{credential_id}/revoke`
- Existing public verification: `GET /api/v1/credentials/verify/{credential_number}`

## Migration

- `0010_credential_revocation`
- Adds `revoked_at`, `revoked_by_id`, and `revocation_reason` to `training_credentials`.

## Run

```powershell
cd C:\NCCT\NCCT-Cooperative-Ecosystem\backend
alembic upgrade head
```

Then restart FastAPI and open Skills & Credentials.
