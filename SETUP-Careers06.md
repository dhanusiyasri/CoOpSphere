# Setup

Backend:
```powershell
cd C:\NCCT\NCCT-Cooperative-Ecosystem\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --port 8000
```
Frontend:
```powershell
cd C:\NCCT\NCCT-Cooperative-Ecosystem\frontend
npm install
npm run dev
```
