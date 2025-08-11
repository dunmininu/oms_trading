#!/bin/bash
set -e

# OMS Trading Docker Entrypoint Script
# This script handles initialization tasks before starting the application

echo "Starting OMS Trading application..."

# Activate virtual environment if it exists
if [ -f "/opt/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source /opt/venv/bin/activate
fi

# Change to backend directory
cd /app/backend

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
echo "Waiting for database..."
/opt/venv/bin/python -c "
import os
import time
try:
    import psycopg2
    from urllib.parse import urlparse
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        parsed = urlparse(database_url)
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:] if parsed.path else 'postgres',
                    connect_timeout=5
                )
                conn.close()
                print('Database is ready!')
                break
            except psycopg2.OperationalError:
                attempt += 1
                print(f'Database not ready, attempt {attempt}/{max_attempts}...')
                time.sleep(2)
        
        if attempt >= max_attempts:
            print('Database connection failed after all attempts')
            exit(1)
    else:
        print('No DATABASE_URL provided, skipping database check')
except ImportError:
    print('psycopg2 not available, skipping database check')
    print('This may cause issues if database operations are required')
"
else
  echo "No DATABASE_URL provided, skipping database check"
fi

# Wait for Redis to be ready
REDIS_WAIT_URL=${REDIS_URL:-$CELERY_BROKER_URL}
if [ -n "$REDIS_WAIT_URL" ]; then
echo "Waiting for Redis..."
/opt/venv/bin/python -c "
import os
import time
import redis
from urllib.parse import urlparse

redis_url = os.environ.get('REDIS_URL') or os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
parsed = urlparse(redis_url)
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        r = redis.Redis(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 6379,
            db=int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0,
            socket_connect_timeout=5
        )
        r.ping()
        print('Redis is ready!')
        break
    except (redis.ConnectionError, redis.TimeoutError):
        attempt += 1
        print(f'Redis not ready, attempt {attempt}/{max_attempts}...')
        time.sleep(2)

if attempt >= max_attempts:
    print('Redis connection failed after all attempts')
    exit(1)
"
else
  echo "No REDIS_URL/CELERY_BROKER_URL provided, skipping redis check"
fi

# Run database migrations
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations..."
  /opt/venv/bin/python manage.py migrate --noinput
else
  echo "Skipping migrations: no DATABASE_URL"
fi

# Collect static files (if not already done)
echo "Collecting static files..."
/opt/venv/bin/python manage.py collectstatic --noinput --clear

# Create cache table if using database cache
echo "Setting up cache tables..."
/opt/venv/bin/python manage.py createcachetable || true

# Create superuser if specified
if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    /opt/venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        first_name='${DJANGO_SUPERUSER_FIRST_NAME:-Admin}',
        last_name='${DJANGO_SUPERUSER_LAST_NAME:-User}'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Load initial data if specified
if [ "$LOAD_INITIAL_DATA" = "true" ]; then
    echo "Loading initial data..."
    /opt/venv/bin/python manage.py loaddata backend/infra/fixtures/initial_data.json || echo "No initial data found"
fi

# Validate deployment settings
if [ "$DJANGO_SETTINGS_MODULE" = "apps.core.settings.prod" ]; then
    echo "Validating production deployment..."
    /opt/venv/bin/python manage.py check --deploy
fi

# Clear expired sessions
echo "Clearing expired sessions..."
/opt/venv/bin/python manage.py clearsessions || true

# Warm up cache if specified
if [ "$WARM_UP_CACHE" = "true" ]; then
    echo "Warming up cache..."
    /opt/venv/bin/python manage.py shell -c "
from django.core.cache import cache
cache.set('health_check', 'ok', 300)
print('Cache warmed up')
" || true
fi

echo "Initialization complete!"

# Execute the main command
exec "$@"
