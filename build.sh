#!/bin/bash
# Build script for Render deployment

echo "Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage_render.py collectstatic --noinput

# Run migrations
python manage_render.py migrate

echo "Build process completed!"