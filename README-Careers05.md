# Careers-05 — Selection & Offer Workflow

Adds the offer stage after recruiter selection.

## Employer / NCCT Admin
- Send an offer only to a `SELECTED` application.
- Set expiry, compensation, employment type and notes.
- See offer status in the application pipeline.

## Trainee
- See pending offer details in My applications.
- Accept or decline a pending offer.
- Acceptance records `ACCEPTED`; decline records `DECLINED`.

## APIs
- `POST /api/v1/careers/applications/{application_id}/offer`
- `POST /api/v1/careers/applications/{application_id}/offer/respond`

## Migration
`0013_career_offer_workflow` adds offer fields to `career_job_applications`.
