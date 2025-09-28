# Render Deployment Checklist

This checklist ensures all necessary steps are completed for a successful deployment to Render.

## Pre-deployment Checklist

- [ ] **Code Repository**
  - [ ] All changes committed and pushed to GitHub
  - [ ] No sensitive information (API keys, passwords) in the codebase
  - [ ] .env file is in .gitignore (only .env.example should be committed)

- [ ] **Environment Variables**
  - [ ] SECRET_KEY generated and secured
  - [ ] GEMINI_API_KEY obtained from Google AI Studio
  - [ ] DEBUG set to False for production

- [ ] **Dependencies**
  - [ ] requirements.txt updated with all necessary packages
  - [ ] No unused or unnecessary dependencies

- [ ] **Configuration Files**
  - [ ] render.yaml properly configured
  - [ ] settings_render.py configured for production
  - [ ] wsgi_render.py properly set up
  - [ ] manage_render.py available

- [ ] **Static Files**
  - [ ] All static files organized properly
  - [ ] Static files can be collected with `collectstatic`

- [ ] **Database**
  - [ ] Database migrations ready
  - [ ] SQLite database works for small deployments
  - [ ] PostgreSQL configuration ready for larger deployments

## Deployment Steps

1. **Fork Repository** (if not using your own)
   - [ ] Fork the repository to your GitHub account

2. **Create Render Account**
   - [ ] Sign up at https://render.com if you don't have an account

3. **Create Web Service**
   - [ ] Log in to Render dashboard
   - [ ] Click "New" → "Web Service"
   - [ ] Connect your GitHub repository
   - [ ] Configure:
     - Name: whatsapp-analytics
     - Region: Choose appropriate region
     - Branch: main (or your preferred branch)
     - Root Directory: whatsapp_django
     - Environment: Python
     - Build Command: `pip install -r requirements.txt && python manage_render.py collectstatic --noinput && python manage_render.py migrate`
     - Start Command: `gunicorn myproject.wsgi_render:application`

4. **Add Environment Variables**
   - [ ] PYTHON_VERSION: 3.11.0
   - [ ] DJANGO_SETTINGS_MODULE: myproject.settings_render
   - [ ] SECRET_KEY: Your generated secret key
   - [ ] GEMINI_API_KEY: Your Gemini API key
   - [ ] DEBUG: False

5. **Deploy**
   - [ ] Click "Create Web Service"
   - [ ] Monitor the build logs for any errors
   - [ ] Wait for deployment to complete

## Post-deployment Verification

- [ ] **Application Health**
  - [ ] Visit your app URL
  - [ ] Check that the main page loads
  - [ ] Test the health check endpoint: `/health/`

- [ ] **Functionality Tests**
  - [ ] Test file upload functionality
  - [ ] Test chat analysis features
  - [ ] Test AI summary generation
  - [ ] Test export features

- [ ] **Performance**
  - [ ] Check application response time
  - [ ] Verify memory usage is within limits
  - [ ] Test with sample data

## Troubleshooting

- **Build Failures**
  - Check build logs in Render dashboard
  - Verify all dependencies in requirements.txt
  - Ensure build command is correct

- **Runtime Errors**
  - Check application logs in Render dashboard
  - Verify environment variables are set correctly
  - Check that the WSGI application starts properly

- **Database Issues**
  - Ensure database migrations run successfully
  - Check database connection settings
  - Verify file permissions for SQLite database

- **Static Files**
  - Ensure WhiteNoise is configured correctly
  - Check that collectstatic runs during build
  - Verify static file URLs work

## Common Issues and Solutions

1. **ModuleNotFoundError**
   - Ensure all dependencies are in requirements.txt
   - Check that the build command installs dependencies

2. **Permission Denied**
   - Check file permissions in repository
   - Ensure database file is writable

3. **Memory Issues**
   - Application is configured with memory optimization
   - Check gunicorn.conf.py settings

4. **Timeout Issues**
   - Adjust timeout settings in gunicorn.conf.py
   - Optimize AI request handling

## Support

For additional help:
- Check Render documentation: https://render.com/docs
- Review Django deployment documentation
- Contact support if issues persist