NCCT Attendance Reports API Backend Patch

Your Swagger screenshot shows the running backend still has the Attendance-02 routes only.
Replace ONLY these two files in your current project:

backend/app/attendance/router.py
backend/app/attendance/schemas.py

Do NOT replace the database or run a migration for this patch.

Then restart FastAPI:
  cd C:\NCCT\NCCT-Cooperative-Ecosystem\backend
  uvicorn app.main:app --reload --port 8000

Verify /docs contains:
  GET /api/v1/attendance/reports
  GET /api/v1/attendance/reports/my
  GET /api/v1/attendance/alerts/low-attendance

main.py already registers the attendance router, so no main.py change is needed.
