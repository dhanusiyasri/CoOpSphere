# Setup

1. Merge this build into the current NCCT project.
2. Run `alembic upgrade head` from `backend`.
3. Start FastAPI without `--reload` initially: `uvicorn app.main:app --port 8000`.
4. In `frontend`, run `npm install` and `npm run dev`.
5. Login as EMPLOYER or NCCT_ADMIN → Careers → Applications → Schedule interview.
6. Login as TRAINEE → Careers → My applications to verify interview details.
