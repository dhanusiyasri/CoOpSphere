@echo off
cd /d %~dp0
if not exist node_modules (
  echo node_modules not found. Run scripts\setup.bat first.
  pause
  exit /b 1
)
npm run dev
