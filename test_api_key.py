import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Test the API key
def test_api_key():
    # Check environment variable
    env_key = os.getenv('GEMINI_API_KEY')
    print(f"Environment variable GEMINI_API_KEY: {env_key}")
    
    # Check Django settings
    django_key = getattr(settings, 'GEMINI_API_KEY', None)
    print(f"Django settings GEMINI_API_KEY: {django_key}")
    
    # Test which one is being used
    api_key = env_key or django_key
    print(f"API key being used: {api_key}")
    
    if not api_key:
        print("❌ No API key found!")
        return False
    
    # Try to initialize the model
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try to initialize the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("✅ Gemini model initialized successfully")
        
        # Try a simple test
        response = model.generate_content("Say hello in one word")
        print(f"✅ API test successful: {response.text.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_key()