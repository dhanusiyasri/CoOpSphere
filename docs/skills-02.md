# Skills-02 — Competency & Skill Passport

A structured competency profile built on the existing trainee identity and digital-literacy profile.

## Scope
- Skill catalogue with cooperative, digital and professional competencies.
- Trainee skill records with 1–5 proficiency.
- Trainer/admin verification and evidence notes.
- Trainee skill passport and role-scoped manager view.
- Skill gaps are skills below working proficiency (3/5).
- Digital literacy remains a separate assessment signal and is displayed on the passport.

## APIs
- `GET /api/v1/skills/passport/catalog`
- `GET /api/v1/skills/passport/my`
- `GET /api/v1/skills/passport`
- `POST /api/v1/skills/passport/assign`

## Migration
`0020_skill_passport` creates `skill_catalog` and `trainee_skills` and adds a small demo baseline for `trainee@ncct.local` when the seeded user exists.
