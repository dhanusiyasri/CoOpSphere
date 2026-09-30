# Careers-04 — Interview Scheduling & Recruiter Pipeline

Adds a practical recruiter workflow on top of Careers-01 through Careers-03.

## Employer / NCCT admin
- Schedule an interview for an application.
- Choose ONLINE, IN_PERSON or PHONE.
- Store date/time, venue or meeting link and notes.
- Scheduling moves the application to INTERVIEW.
- Cancel an interview and return the application to SHORTLISTED.
- Continue to update application status through the existing pipeline.

## Trainee
- Application history now shows scheduled interview date/time, mode and venue/link.

## APIs
- `POST /api/v1/careers/applications/{application_id}/interview`
- `POST /api/v1/careers/applications/{application_id}/interview/cancel`

## Database
Migration `0012_career_interview_scheduling` adds interview scheduling and application update fields.
