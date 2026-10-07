#!/bin/sh
set -e

echo "[ResumeIQ Entrypoint] Checking database connection..."
python -c "
import os, time, sys
db_url = os.getenv('DATABASE_URL', '')
if 'postgres' in db_url:
    clean_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')
    for i in range(30):
        try:
            import psycopg2
            conn = psycopg2.connect(clean_url)
            conn.close()
            print('[ResumeIQ Entrypoint] Database connection verified.')
            sys.exit(0)
        except Exception as e:
            time.sleep(1)
    print('[ResumeIQ Entrypoint] Timed out waiting for database:', e)
    sys.exit(1)
" || true

echo "[ResumeIQ Entrypoint] Running Alembic migrations to head..."
alembic upgrade head
echo "[ResumeIQ Entrypoint] Migrations complete."

exec "$@"
