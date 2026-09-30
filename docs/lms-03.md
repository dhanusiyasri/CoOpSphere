# LMS-03 — Training Certificates & Credentials

## Scope
LMS-03 adds a persistent course-completion credential workflow on top of LMS-01 lesson progress and LMS-02 assessments.

## Eligibility
A trainee can claim a credential for an enrolled course when:

1. Every course lesson is marked `COMPLETED`.
2. Every published assessment attached to the course has a latest attempt with result `PASS`.

If a course has no published assessments, completion of all lessons is sufficient.

## API

- `GET /api/v1/credentials/my-credentials`
- `GET /api/v1/credentials/{credential_id}`
- `GET /api/v1/credentials/courses/{course_id}/eligibility`
- `POST /api/v1/credentials/courses/{course_id}/issue`

Credential issue is idempotent for a trainee/course pair: if a credential already exists, the existing record is returned.

## Data

Migration: `0006_training_credentials`

Table: `training_credentials`

The record stores a unique credential number, course title snapshot, completion counts, assessment score summary, issue timestamp, and status.

## UI

- `LMS` shows a **Claim completion credential** action when lesson progress reaches 100%.
- `Skills & Credentials` shows issued credentials and their credential numbers, completion counts, assessment score, and issue date.

## Not included

PDF certificate generation, QR verification, public credential verification, revocation workflow, issuer administration, and digital-wallet integrations are intentionally deferred to later slices.
