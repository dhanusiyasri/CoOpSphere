# Skills-01 — Digital Literacy Assessment

Proposed vertical slice aligned to the NCCT requirement for digital literacy.

## Trainee
- Complete a 10-question practical digital literacy assessment.
- Receive percentage score and BASIC / INTERMEDIATE / ADVANCED level.
- Previous attempts remain visible.
- The latest level updates the trainee participant profile.

## Managers
- View assessment results within role scope.
- NCCT Admin sees all results; Institute Admin is institution-scoped; Trainer sees results for assigned batches.

## API
- GET `/api/v1/skills/digital-literacy/questions`
- POST `/api/v1/skills/digital-literacy/attempts`
- GET `/api/v1/skills/digital-literacy/my-attempts`
- GET `/api/v1/skills/digital-literacy/attempts`

## Migration
- `0019_digital_literacy`
