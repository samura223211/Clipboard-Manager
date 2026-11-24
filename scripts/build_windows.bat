@echo off
setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
  echo Warning: venv not found, using system Python.
)

"%PY%" scripts\build_app.py %*
if errorlevel 1 exit /b %errorlevel%
endlocal
