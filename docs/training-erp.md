# Training ERP

## Scope in this slice

This module is the first end-to-end business workflow on top of the common foundation:

`Programme → Batch → Nomination (ERP-03) → Approval/Reject → Enrollment`

## Backend

- `app/training/models.py` — programme, batch, nomination, enrollment tables
- `app/training/schemas.py` — request/response validation
- `app/training/service.py` — duplicate checks, capacity checks and approval logic
- `app/training/router.py` — REST API
- `alembic/versions/0002_training_erp.py` — database migration

## API

All routes are under `/api/v1/training`.

- `GET /programmes`
- `POST /programmes`
- `GET /batches`
- `POST /batches`
- `GET /nominations`
- `POST /nominations`
- `POST /nominations/{id}/approve`
- `POST /nominations/{id}/reject`
- `GET /enrollments`
- `POST /enrollments`

## Demo flow

1. Sign in as `admin@ncct.local` / `Admin@123`.
2. Open **Training ERP**.
3. Create a programme.
4. Create a batch for that programme.
5. Submit a nomination using a trainee account, or create one through the API as an admin/trainer.
6. Approve the nomination as admin/trainer.
7. Verify the enrollment in the enrollment register.

## Role rules

- `NCCT_ADMIN`, `INSTITUTE_ADMIN`, and `TRAINER`: create programmes/batches, view the operational queue, approve nominations.
- Programme creation requires selecting an active training provider; institute administrators are restricted to their own institution.
- `TRAINEE`: submit nominations for themselves and view their own nominations/enrollments.
- `EMPLOYER`: can authenticate against the common foundation but does not manage Training ERP records.

## Business safeguards

- Programme code is unique.
- Batch code is unique within a programme.
- A trainee cannot be nominated twice for the same batch.
- A trainee cannot be enrolled twice in the same batch.
- Approval creates an enrollment automatically.
- Approval checks batch capacity.
- A rejected nomination cannot be enrolled.


## ERP-03 — Nomination Management

ERP-03 is a visible Training ERP section for both trainees and operational managers.

- `TRAINEE` users can submit a nomination for themselves.
- `NCCT_ADMIN`, `INSTITUTE_ADMIN`, and `TRAINER` users can create a nomination for a trainee by user ID.
- The backend verifies that the selected account has the `TRAINEE` role.
- The UI shows available batch capacity and blocks duplicate active nominations.
- A previously rejected nomination can be resubmitted.
- The nomination management queue is visible in the same section.
- Managers can approve (creating enrollment) or reject with an optional reason.

This is intentionally part of the main Training ERP screen; it is not hidden behind a trainee-only view.

## ERP-06 — Participant Management

ERP-06 maintains the participant master profile used by nomination, training, skills and employment modules. Profiles are linked one-to-one to seeded `TRAINEE` users and include participant code, participant type, phone, designation, organization, education, district/state, digital literacy level, experience and profile status.

The UI exposes a **Participant Management** section with profile creation/update and a participant register. Managers can maintain any trainee profile; a trainee can maintain only their own profile.
