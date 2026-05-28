#!/bin/bash
# ── Tutlee Backend Setup ──────────────────────────────────────────────────────
# Run this once from inside the backend/ folder:
#   cd backend
#   chmod +x setup.sh && ./setup.sh

set -e

echo "==> Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Running migrations..."
python manage.py migrate

echo "==> Seeding demo data..."
python manage.py seed

echo ""
echo "==> Setup complete!"
echo ""
echo "Demo accounts:"
echo "  Admin   : admin@tutlee.com   / admin123"
echo "  Tutors  : kwame@tutlee.com   / tutor123"
echo "            nana@tutlee.com    / tutor123"
echo "            ama@tutlee.com     / tutor123"
echo "  Learners: amara@tutlee.com   / learner123"
echo "            zara@tutlee.com    / learner123"
echo ""
echo "==> Starting development server on http://127.0.0.1:8000 ..."
python manage.py runserver
