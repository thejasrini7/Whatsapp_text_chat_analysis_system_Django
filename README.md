# WhatsApp Group Analytics - Render Deployment

This application is configured for deployment on Render with the following entry points:

## Entry Points

1. **WSGI Application**: [wsgi.py](file://d:/AgroAnalytics_Intern/Whatsapp_group_analytics_project_django_current/Whatsapp_group_analytics_project_django/wsgi.py) - Contains the WSGI application entry point
2. **Settings**: [settings.py](file://d:/AgroAnalytics_Intern/Whatsapp_group_analytics_project_django_current/Whatsapp_group_analytics_project_django/settings.py) - Django settings configuration
3. **URLs**: [urls.py](file://d:/AgroAnalytics_Intern/Whatsapp_group_analytics_project_django_current/Whatsapp_group_analytics_project_django/urls.py) - URL routing configuration

## Deployment Configuration

The application is configured with:
- **Procfile**: Specifies the web process command
- **render.yaml**: Render deployment configuration
- **runtime.txt**: Specifies Python version
- **requirements.txt**: Python dependencies

## Render Deployment Commands

Render will use the following commands:
- **Build**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start**: `gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120`

## Environment Variables

The following environment variables should be set in the Render dashboard:
- `SECRET_KEY`: Django secret key
- `GEMINI_API_KEY`: Google Gemini API key
- `DEBUG`: Set to `False` for production