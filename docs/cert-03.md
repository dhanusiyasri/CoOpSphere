# CERT-03 — Credential Issuance

Adds manager-controlled credential issuance to the credential readiness queue.

## Workflow

Training ERP → LMS lesson completion/assessment → Attendance advisory → CERT-02 readiness → manager issues credential → registry → public verification.

Attendance remains advisory and is not a hard issuance gate. Lesson completion and published assessment passes remain the issuance requirements.

## API

- `POST /api/v1/credentials/readiness/{trainee_id}/{course_id}/issue` — manager-scoped issuance
- Existing `GET /api/v1/credentials/verify/{credential_number}` remains the public verification endpoint.

## Audit

Migration `0011_credential_issuance_audit` adds `training_credentials.issued_by_id` so the issuing user is persisted.

## Duplicate handling

A trainee/course pair can have one credential because of the existing unique constraint. If a credential already exists, the manager cannot silently create another one.

## Test

1. Run `alembic upgrade head`.
2. Start the backend and open `/docs`.
3. Confirm the new manager issuance endpoint appears under Skills & Credentials.
4. Login as `NCCT_ADMIN`.
5. Open Skills & Credentials → Credential readiness.
6. For a `READY` row, click **Issue credential**.
7. Confirm it moves into Registry.
8. Open the public verification link for the credential.
9. Verify the credential is active and later revocation invalidates it.
