# Deploying to Render

This document provides instructions for deploying the WhatsApp Group Analytics application to Render.

## Prerequisites

1. A Render account (https://render.com)
2. A Gemini API key (https://ai.google.dev/)

## Deployment Steps

### Option 1: Deploy with Docker (Recommended)

1. Fork this repository to your GitHub account
2. Log in to your Render dashboard
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: whatsapp-analytics
   - Region: Choose the region closest to your users
   - Branch: main (or your preferred branch)
   - Root Directory: Leave empty
   - Environment: Docker
   - Dockerfile Path: Dockerfile
   - Plan: Free or Starter (depending on your needs)

6. Add environment variables in the "Advanced" section:
   - SECRET_KEY: Generate a secure secret key
   - GEMINI_API_KEY: Your Gemini API key
   - DEBUG: False

7. Click "Create Web Service"

### Option 2: Deploy with Render's Native Python Environment

1. Fork this repository to your GitHub account
2. Log in to your Render dashboard
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - Name: whatsapp-analytics
   - Region: Choose the region closest to your users
   - Branch: main (or your preferred branch)
   - Root Directory: whatsapp_django
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn myproject.wsgi_render:application`

6. Add environment variables in the "Advanced" section:
   - PYTHON_VERSION: 3.11.0
   - DJANGO_SETTINGS_MODULE: myproject.settings_render
   - SECRET_KEY: Generate a secure secret key
   - GEMINI_API_KEY: Your Gemini API key
   - DEBUG: False

7. Click "Create Web Service"

## Environment Variables

The following environment variables need to be set in your Render dashboard:

- `SECRET_KEY`: Django secret key (generate a secure one)
- `GEMINI_API_KEY`: Your Gemini API key for AI features
- `DEBUG`: Set to `False` for production
- `DATABASE_URL`: For production, consider using a PostgreSQL database

## Notes

1. The application uses SQLite database by default, which is suitable for small deployments. For production usage, consider upgrading to PostgreSQL.

2. Static files are served using WhiteNoise, which is suitable for small to medium deployments.

3. The application includes memory optimization settings in the gunicorn configuration to work within Render's free tier limitations.

4. Make sure to set up your domain and SSL certificate in the Render dashboard after deployment.

## Troubleshooting

If you encounter issues:

1. Check the logs in your Render dashboard
2. Ensure all environment variables are correctly set
3. Verify that your Gemini API key is valid and has sufficient quota
4. Check that the build process completes successfully

For additional support, refer to the [Render documentation](https://render.com/docs).