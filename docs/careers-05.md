# Careers-05 — Selection & Offer Workflow

Adds a practical offer stage after recruiter selection.

## Employer / NCCT admin
- Send an offer only to a SELECTED application.
- Store expiry, compensation, employment type and notes.
- See offer state in the application pipeline.

## Trainee
- See pending offer details in My applications.
- Accept or decline a pending offer.
- Acceptance keeps the application in SELECTED while recording the offer response.

## APIs
- `POST /api/v1/careers/applications/{application_id}/offer`
- `POST /api/v1/careers/applications/{application_id}/offer/respond`

## Database
Migration `0013_career_offer_workflow` adds persistent offer fields to `career_job_applications`.
