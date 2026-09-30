# Careers-01 — Employment Exchange

This slice connects trained NCCT trainees with published cooperative-sector job opportunities.

## Trainee flow
- Open Careers
- Review published jobs
- Select a role
- Submit an optional cover note
- Track application status

## Employer flow
- Login as `employer@ncct.local`
- Publish a job opportunity
- Review applications
- Update application status: APPLIED, SHORTLISTED, INTERVIEW, SELECTED, REJECTED

## APIs
- `GET /api/v1/careers/jobs`
- `POST /api/v1/careers/jobs`
- `GET /api/v1/careers/jobs/{job_id}`
- `POST /api/v1/careers/jobs/{job_id}/apply`
- `GET /api/v1/careers/my-applications`
- `GET /api/v1/careers/employer-applications`
- `POST /api/v1/careers/applications/{application_id}/status`

This is an MVP employment exchange. Resume uploads, matching/ranking, interview scheduling and notifications are deliberately deferred to later slices.
