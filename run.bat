@echo off
REM Perde - one-click launcher for Windows
cd /d "%~dp0"

where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version >nul 2>nul || (
  echo Python 3.10+ is required. Install it from https://www.python.org/downloads/ and tick "Add to PATH".
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating virtual environment...
  %PY% -m venv .venv || (pause & exit /b 1)
)

echo Installing dependencies (first run takes a minute)...
.venv\Scripts\python -m pip install --quiet --disable-pip-version-check -r requirements.txt || (pause & exit /b 1)

echo Starting Perde at http://localhost:8501 ...
start "" cmd /c "timeout /t 5 >nul & start http://localhost:8501"
.venv\Scripts\python -m streamlit run app.py --server.headless=true
pause
