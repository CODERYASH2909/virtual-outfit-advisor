#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python - << 'PYEOF'
import time, os, sys
import psycopg2
for i in range(30):
    try:
        psycopg2.connect(
            dbname=os.environ.get("DB_NAME", "voa_db"),
            user=os.environ.get("DB_USER", "voa_user"),
            password=os.environ.get("DB_PASSWORD", "voa_password"),
            host=os.environ.get("DB_HOST", "db"),
            port=os.environ.get("DB_PORT", "5432"),
        ).close()
        print("Database is ready.")
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Database not reachable after 30s.")
sys.exit(1)
PYEOF

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
