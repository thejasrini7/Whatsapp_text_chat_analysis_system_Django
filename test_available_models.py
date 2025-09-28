import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

def test_available_models():
    try:
        import google.generativeai as genai
        from django.conf import settings
        
        # Configure Gemini AI
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            print("❌ No API key found!")
            return
            
        print(f"Using API key: {api_key[:10]}...{api_key[-4:]}")
        genai.configure(api_key=api_key)
        
        # List available models
        print("Listing available models...")
        try:
            models = genai.list_models()
            print("Available models:")
            valid_models = []
            for model in models:
                print(f"  - {model.name}")
                # Check if it's a valid generative model
                if 'generateContent' in getattr(model, 'supported_generation_methods', []):
                    valid_models.append(model.name)
            
            print(f"\nValid generative models: {valid_models}")
            
            # Test a few models
            test_models = ['gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro', 'gemini-1.5-flash', 'gemini-1.0-flash']
            working_models = []
            
            for model_name in test_models:
                if model_name in valid_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content("Say 'hello' in one word")
                        print(f"✅ {model_name}: {response.text.strip()}")
                        working_models.append(model_name)
                    except Exception as e:
                        print(f"❌ {model_name}: {e}")
                else:
                        print(f"⚠️  {model_name}: Not in available models list")
            
            print(f"\nWorking models: {working_models}")
            if working_models:
                print(f"Recommended model: {working_models[0]}")
            
        except Exception as e:
            print(f"Could not list models: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_available_models()