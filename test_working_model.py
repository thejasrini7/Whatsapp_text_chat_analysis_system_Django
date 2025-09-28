import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

def test_working_model():
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
        
        # Test some available models that support generateContent
        test_models = [
            'gemini-2.0-flash',
            'gemini-2.0-flash-001', 
            'gemini-2.5-flash',
            'gemini-2.5-flash-preview-05-20',
            'gemini-flash-latest',
            'gemini-pro-latest'
        ]
        
        working_model = None
        for model_name in test_models:
            try:
                print(f"Testing {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'hello' in one word")
                print(f"✅ {model_name}: SUCCESS - {response.text.strip()}")
                working_model = model_name
                break
            except Exception as e:
                print(f"❌ {model_name}: {str(e)[:100]}...")
        
        if working_model:
            print(f"\n✅ Recommended working model: {working_model}")
            
            # Test with a longer prompt to make sure it works well
            try:
                test_prompt = "Summarize this message in 5 words: 'This is a great day for testing AI models'"
                response = model.generate_content(test_prompt)
                print(f"✅ Extended test: {response.text.strip()}")
            except Exception as e:
                print(f"❌ Extended test failed: {e}")
        else:
            print("\n❌ No working models found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_working_model()