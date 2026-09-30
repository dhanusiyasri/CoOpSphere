# Intelligence-03 — AI Training & Career Assistant

## Scope

Adds a grounded assistant to the existing Intelligence module. The assistant answers from current NCCT database records and does not use forecasts or fabricate external trainee, training or employment facts.

## API

`POST /api/v1/intelligence/assistant`

Roles: `TRAINEE`, `NCCT_ADMIN`, `INSTITUTE_ADMIN`, `TRAINER`.

## Trainee intents

- Learning progress across active published courses and lessons.
- Attendance rate and present/late/absent counts.
- Issued credentials and credential numbers/status.
- Latest published employment opportunities.
- General help with supported NCCT topics.

## Analyst intents

- Operational training snapshot.
- Low-attendance trainees below the 75% threshold.
- Employment exchange job/application/selected counts.

Institute admins and trainers receive responses scoped to their permitted trainee population. NCCT admins receive the overall scope.

## UI

Adds an **AI Assistant** tab to the existing Intelligence dashboard with suggested questions, free-text questions, grounded responses and source labels.

## Database

No new migration is required. The assistant reads existing Training ERP, LMS, Attendance, Credentials and Careers tables.
