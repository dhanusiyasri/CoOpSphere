@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run scripts\setup.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe --version >nul 2>&1
if errorlevel 1 (
  echo Virtual environment is invalid. Run scripts\setup.bat to recreate it.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
