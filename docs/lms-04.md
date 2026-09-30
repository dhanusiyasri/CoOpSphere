# LMS-04 — Credential Verification & Certificate PDF

This slice extends LMS-03 without changing the credential database schema.

## Features
- Public credential verification endpoint using the credential number.
- Public browser verification page at `/verify/{credential_number}`.
- Trainee-only certificate PDF download from Skills & Credentials.
- Certificate PDF contains a QR code linking to the public verification page.
- Existing LMS-03 credential records remain unchanged.

## Endpoints
- `GET /api/v1/credentials/verify/{credential_number}` — public verification.
- `GET /api/v1/credentials/{credential_id}/certificate.pdf` — authenticated trainee download.

## Dependencies
- reportlab
- qrcode

Set `FRONTEND_BASE_URL` in `.env` when the frontend is hosted at a URL other than `http://localhost:5173`.
