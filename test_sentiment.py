#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.sentiment_analyzer import analyze_sentiment

def test_sentiment_analysis():
    print("Testing sentiment analysis...")
    
    # Load chat data
    chat_data = load_all_chats()
    print(f"Available groups: {list(chat_data.keys())}")
    
    if not chat_data:
        print("No chat data found!")
        return
    
    # Test with first group
    group_name = list(chat_data.keys())[0]
    messages = chat_data[group_name]['messages'][:10]  # Test with first 10 messages
    print(f"Testing with {len(messages)} messages from '{group_name}'")
    
    # Test sentiment analysis
    try:
        result = analyze_sentiment(messages)
        print("✅ Sentiment analysis successful!")
        print(f"Result keys: {list(result.keys())}")
        print(f"Overall sentiment: {result.get('overall_sentiment')}")
        print(f"Sentiment breakdown: {result.get('sentiment_breakdown')}")
        
        if 'daily_sentiment' in result and result['daily_sentiment']:
            print(f"Daily sentiment data available: {len(result['daily_sentiment'])} days")
        
        if 'user_sentiment' in result and result['user_sentiment']:
            print(f"User sentiment data available: {len(result['user_sentiment'])} users")
            
        return True
    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sentiment_analysis()