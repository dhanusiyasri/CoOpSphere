# CERT-04 — Credential Wallet & Public Verification

## Purpose
Extend issued credentials into a trainee-facing wallet with QR-based public verification and make revoked credentials explicitly show as invalid rather than appearing as a generic not-found error.

## Included
- Trainee credential wallet shows a verification QR for active credentials.
- Trainee can copy a public verification link.
- Public verification returns `valid=false` for revoked credentials and includes revocation details.
- Public QR endpoint: `GET /api/v1/credentials/verify/{credential_number}/qr`.
- No database migration.

## Verification behavior
- ISSUED -> valid=true.
- REVOKED -> valid=false, with status and revocation details.
- Unknown credential -> 404.

## Test
1. Login as trainee and open Skills & Credentials.
2. Confirm an active credential displays a QR and copy-link action.
3. Open public verification and confirm it shows a valid credential.
4. As a manager, revoke that credential.
5. Reopen the public verification URL and confirm it explicitly shows the credential is revoked and not valid.
