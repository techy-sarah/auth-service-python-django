#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

echo "Collecting static files..."
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py collectstatic --noinput

echo "Running migrations..."
DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate

echo "Done!"