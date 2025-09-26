#!/usr/bin/env python3

"""
Test script to verify Gemini API integration
"""

import sys
import os
import django

# Add the project path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import google.generativeai as genai
from myproject.settings import GEMINI_API_KEY

def test_gemini_api():
    """Test basic Gemini API functionality"""
    try:
        # Configure Gemini AI
        api_key = GEMINI_API_KEY
        print(f"Using API key: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
        
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Test basic functionality
        test_prompt = """
        Analyze the sentiment of this message: "I'm really happy today! This is great news!"
        
        Respond in JSON format:
        {
            "sentiment": "positive/neutral/negative",
            "confidence": 0.95,
            "reason": "Brief explanation"
        }
        """
        
        print("Testing Gemini API...")
        response = model.generate_content(test_prompt)
        print("✅ API Response received!")
        print("Response:", response.text)
        
        return True
        
    except Exception as e:
        print(f"❌ API Test failed: {e}")
        return False

def test_sentiment_analyzer():
    """Test the sentiment analyzer function"""
    try:
        from chatapp.sentiment_analyzer import batch_analyze_sentiment_with_gemini
        
        test_messages = [
            {'message': 'I love this!', 'sender': 'Alice', 'timestamp': '2024-01-01 10:00:00'},
            {'message': 'This is terrible', 'sender': 'Bob', 'timestamp': '2024-01-01 10:01:00'}
        ]
        
        print("\\nTesting sentiment analyzer...")
        results = batch_analyze_sentiment_with_gemini(test_messages)
        print("✅ Sentiment analysis completed!")
        print("Results:", results)
        
        return True
        
    except Exception as e:
        print(f"❌ Sentiment analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini Integration\\n")
    
    # Test API
    api_success = test_gemini_api()
    
    # Test sentiment analyzer
    analyzer_success = test_sentiment_analyzer()
    
    if api_success and analyzer_success:
        print("\\n🎉 All tests passed! Gemini integration is working.")
    else:
        print("\\n⚠️  Some tests failed. Check the error messages above.")