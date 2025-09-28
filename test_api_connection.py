import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_connection():
    # Test if the API key is properly configured
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return False
    
    print(f"API Key exists: {bool(api_key)}")
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured successfully")
        
        # Try to initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Model 'gemini-2.0-flash' initialized successfully")
        
        # Try a simple test prompt
        test_prompt = "Say 'Hello, World!' in 5 different languages."
        response = model.generate_content(test_prompt)
        print("✅ API call successful")
        print(f"Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

# Run the test
if __name__ == "__main__":
    test_api_connection()