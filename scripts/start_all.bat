@echo off
setlocal
cd /d %~dp0\..
start "NCCT Backend" cmd /k "cd /d %CD%\backend && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
start "NCCT Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"
timeout /t 3 /nobreak >nul
start http://localhost:5173
