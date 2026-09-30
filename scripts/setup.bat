@echo off
setlocal
cd /d %~dp0\..

echo ========================================
echo NCCT Local Development Setup
echo ========================================

where python >nul 2>&1 || (echo Python not found. Install Python 3.11+ & pause & exit /b 1)
where node >nul 2>&1 || (echo Node.js not found. Install Node.js 20+ & pause & exit /b 1)
where psql >nul 2>&1 || (echo PostgreSQL psql not found in PATH. Add PostgreSQL bin to PATH. & pause & exit /b 1)

if exist backend\.venv\Scripts\python.exe (
  backend\.venv\Scripts\python.exe --version >nul 2>&1
  if errorlevel 1 (
    echo Existing backend virtual environment is invalid. Recreating it...
    rmdir /s /q backend\.venv
  )
)

if not exist backend\.venv\Scripts\python.exe (
  echo Creating Python virtual environment...
  python -m venv backend\.venv
)
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 goto :fail

if not exist backend\.env (
  copy backend\.env.example backend\.env >nul
  echo Created backend\.env - update the PostgreSQL password if required.
)

echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 goto :fail
cd ..

echo Running database migrations...
cd backend
call .venv\Scripts\activate.bat
alembic upgrade head
if errorlevel 1 goto :fail
python -m app.seed
if errorlevel 1 goto :fail
cd ..

echo.
echo Setup complete.
echo Run scripts\start_all.bat to start the platform.
pause
exit /b 0

:fail
echo.
echo SETUP FAILED. Review the error above.
pause
exit /b 1
