#!/usr/bin/env bash
set -o errexit

python manage.py collectstatic --noinput --clear
python -m gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout ${GUNICORN_TIMEOUT:-180}
