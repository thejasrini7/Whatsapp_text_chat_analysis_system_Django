"""
Test script to verify Render deployment setup
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings_render')

def test_settings():
    """Test that settings can be loaded properly"""
    try:
        django.setup()
        print("✅ Django settings loaded successfully")
        
        # Test database configuration
        print(f"✅ Database engine: {settings.DATABASES['default']['ENGINE']}")
        
        # Test static files configuration
        print(f"✅ Static root: {settings.STATIC_ROOT}")
        print(f"✅ Static URL: {settings.STATIC_URL}")
        
        # Test middleware
        print(f"✅ Middleware count: {len(settings.MIDDLEWARE)}")
        
        # Test installed apps
        print(f"✅ Installed apps: {', '.join(settings.INSTALLED_APPS)}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading Django settings: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set"""
    required_vars = ['SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   These will use default values in settings_render.py")
    else:
        print("✅ All required environment variables are set or have defaults")
    
    return len(missing_vars) == 0

if __name__ == "__main__":
    print("Testing Render deployment setup...")
    print("=" * 50)
    
    settings_ok = test_settings()
    env_ok = test_environment_variables()
    
    print("=" * 50)
    if settings_ok and env_ok:
        print("✅ All tests passed! Ready for Render deployment")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above")
        sys.exit(1)