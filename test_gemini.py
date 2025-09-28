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

        # List available models
        print("Listing available models...")
        try:
            models = genai.list_models()
            print("Available models:")
            for model in models:
                print(f"  - {model.name}")
        except Exception as e:
            print(f"Could not list models: {e}")

        # Try different model names
        model_names = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest', 'gemini-2.5-flash']

        for model_name in model_names:
            try:
                print(f"\nTrying model: {model_name}")
                model = genai.GenerativeModel(model_name)

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
                print(f"✅ SUCCESS with model: {model_name}")
                return True

            except Exception as e:
                print(f"❌ Failed with {model_name}: {e}")
                continue

        print("❌ All models failed")
        return False

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

def test_weekly_summary():
    """Test the weekly summary generation"""
    try:
        from chatapp.summary_generator import generate_weekly_summary

        # Create test messages spanning multiple weeks
        test_messages = [
            {'message': 'Hello everyone!', 'sender': 'Alice', 'timestamp': '01/01/24, 10:00 AM'},
            {'message': 'How are you doing?', 'sender': 'Bob', 'timestamp': '01/02/24, 11:00 AM'},
            {'message': 'Great meeting today', 'sender': 'Charlie', 'timestamp': '01/08/24, 2:00 PM'},
            {'message': 'Lets discuss the project', 'sender': 'Alice', 'timestamp': '01/09/24, 3:00 PM'},
            {'message': 'Meeting scheduled for tomorrow', 'sender': 'Bob', 'timestamp': '01/15/24, 9:00 AM'},
        ]

        print("\\nTesting weekly summary generation...")
        summaries = generate_weekly_summary(test_messages, None, None)
        print("✅ Weekly summary generation completed!")
        print(f"Generated {len(summaries)} weekly summaries")

        for i, summary in enumerate(summaries):
            print(f"Week {i+1}: {summary['date_range']} - {summary['summary'][:100]}...")

        return True

    except Exception as e:
        print(f"❌ Weekly summary test failed: {e}")
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