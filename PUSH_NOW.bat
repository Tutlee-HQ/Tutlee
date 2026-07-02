@echo off
echo Pushing all Tutlee fixes to GitHub...
cd /d "%~dp0"
git config user.email "dahomaconsulting@gmail.com"
git config user.name "Tutlee"
git add api.js
git add index.html
git add admin.html
git add backend/tutlee/urls.py
git add backend/study_rings/views.py
git add backend/sessions_app/models.py
git add backend/sessions_app/serializers.py
git add backend/sessions_app/views.py
git add backend/sessions_app/urls.py
git add "backend/sessions_app/migrations/0002_message.py"
git add push_changes.py
git commit -m "Fix booking, study ring join, page reload, messaging, skill passport, KYT media"
git push origin main
if %ERRORLEVEL% NEQ 0 (
  git push origin master
)
echo.
echo Done! Check above for any errors.
pause
