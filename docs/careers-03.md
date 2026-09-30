# Careers-03 — Resume/CV & Recruiter Search

## Scope

Careers-03 adds two end-to-end capabilities on top of Careers-02:

1. A trainee can generate a PDF CV from their NCCT career profile, participant information and issued NCCT credentials.
2. Employers and NCCT administrators can search visible trainee profiles by name/profile text, skill, location, minimum experience and education.

## APIs

- `GET /api/v1/careers/profile/resume.pdf` — trainee CV PDF
- `GET /api/v1/careers/candidate-search` — employer/admin candidate directory
- `GET /api/v1/careers/candidate-search/{trainee_id}` — employer/admin candidate profile

## Privacy

Only profiles with `profile_visibility=VISIBLE` are returned to employer searches. The existing application-level candidate-profile authorization remains in place.

## Database

No new migration is required. Careers-03 reads the existing `career_profiles`, `training_participant_profiles`, and `training_credentials` records.

## Demo flow

Trainee: Careers → My career profile → Download CV PDF.

Employer: Careers → Candidate directory → filter → View profile.
