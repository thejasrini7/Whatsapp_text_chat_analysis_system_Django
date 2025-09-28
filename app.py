"""
Simple WSGI application entry point for Render deployment
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings_render')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()