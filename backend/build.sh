#!/usr/bin/env bash
# Render build script — runs on every deploy
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Reset DB schema so migrate always starts clean
python - <<'PYEOF2'
import os, psycopg2
db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print('[BUILD] No DATABASE_URL — skipping schema reset')
else:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('DROP SCHEMA public CASCADE')
    cur.execute('CREATE SCHEMA public')
    cur.execute('GRANT ALL ON SCHEMA public TO public')
    cur.execute('GRANT ALL ON SCHEMA public TO postgres')
    conn.close()
    print('[BUILD] Schema reset complete — all tables dropped')
PYEOF2

python manage.py migrate
python manage.py seed || echo "Seed already done or skipped"
