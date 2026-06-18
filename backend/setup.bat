@echo off
REM ── Tutlee Backend Setup (Windows) ───────────────────────────────────────────
REM Run this once from inside the backend\ folder:
REM   cd backend
REM   setup.bat

echo =^> Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Could not create virtual environment. Make sure Python is installed.
    pause & exit /b 1
)

echo =^> Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Package installation failed. See error above.
    pause & exit /b 1
)

echo =^> Running migrations...
venv\Scripts\python.exe manage.py migrate
if errorlevel 1 (
    echo ERROR: Migrations failed.
    pause & exit /b 1
)

echo =^> Seeding demo data...
venv\Scripts\python.exe manage.py seed

echo.
echo =^> Setup complete!
echo.
echo Demo accounts:
echo   Admin   : admin@tutlee.com   / admin123
echo   Tutors  : kwame@tutlee.com   / tutor123
echo   Learners: amara@tutlee.com   / learner123
echo.
echo =^> Starting server on http://127.0.0.1:8000 ...
echo    Open your browser at http://127.0.0.1:8000
echo    Press Ctrl+C to stop the server.
echo.
venv\Scripts\python.exe manage.py runserver
pause
