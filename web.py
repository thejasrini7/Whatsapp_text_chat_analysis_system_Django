"""
Simple web application entry point for Render deployment
"""
import os
import sys

# Add the whatsapp_django directory to Python path
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp_django')
sys.path.insert(0, project_dir)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings_render')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application  # Alias for Render compatibility