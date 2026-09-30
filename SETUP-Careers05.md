# Careers-05 setup

1. Merge this project into the current NCCT project.
2. Run the new migration:

```powershell
cd C:\NCCT\NCCT-Cooperative-Ecosystem\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

3. Verify:

```powershell
alembic current
```

Expected head: `0013_career_offer_workflow`.

4. Start backend without reload for initial verification:

```powershell
uvicorn app.main:app --port 8000
```

5. Start frontend:

```powershell
cd C:\NCCT\NCCT-Cooperative-Ecosystem\frontend
npm install
npm run dev
```

No seed reset is required. Existing applications remain unchanged; offer fields start empty.
