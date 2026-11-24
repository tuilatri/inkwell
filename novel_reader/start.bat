@echo off
REM Inkwell Novel Reader — double-click launcher for Windows Explorer.
REM Always executes via cmd.exe (never "opens in VS Code" like a .py file).
cd /d "%~dp0"

set "PY=%~dp0backend\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Backend venv not found: %PY%
  echo Run setup first: cd backend ^&^& python -m venv .venv ^&^& pip install -e ".[test]"
  pause
  exit /b 1
)

"%PY%" "%~dp0start.py" --no-browser %*
set "RC=%errorlevel%"
echo.
echo Inkwell launcher exited with code %RC%. See logs in "%~dp0logs".
echo Press any key to close this window.
pause
