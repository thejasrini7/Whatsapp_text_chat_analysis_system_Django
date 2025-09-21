#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Change to Django project directory
cd myproject

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate