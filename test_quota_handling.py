import os
import sys
import django
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.utils import filter_messages_by_date
from chatapp.summary_generator import generate_weekly_summary, generate_with_gemini

def test_quota_handling():
    print("=== Testing Quota Handling ===")
    
    # Load chat data
    chat_data = load_all_chats()
    
    # Look for the specific group
    group_name = "Whatsapp Chat With Unofficial Aids C"
    if group_name not in chat_data:
        print(f"Group '{group_name}' not found!")
        return
    
    print(f"Testing group: {group_name}")
    
    # Get messages
    messages = chat_data[group_name]['messages']
    print(f"Total messages in group: {len(messages)}")
    
    # Test with a small date range to avoid too many API calls
    start_date_str = "2024-06-03"  # The specific week user mentioned
    end_date_str = "2024-06-09"
    
    print(f"\nFiltering messages for date range: {start_date_str} to {end_date_str}")
    
    # Use the same filtering logic as in views.py
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after filtering: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages found after filtering!")
        return
    
    # Test the generate_with_gemini function directly
    print("\nTesting generate_with_gemini function...")
    test_prompt = "Say hello in one word"
    response = generate_with_gemini(test_prompt)
    print(f"Direct API response: {response}")
    
    # Check what type of response we get
    if response == "QUOTA_EXCEEDED":
        print("✅ Got QUOTA_EXCEEDED response")
    elif response == "API_ERROR":
        print("⚠️ Got API_ERROR response")
    else:
        print(f"✅ Got normal response: {response[:50]}...")
    
    # Now test generate_weekly_summary with this small range
    print(f"\nGenerating weekly summary for the test week...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    
    if weekly_summaries:
        summary = weekly_summaries[0]
        print(f"Generated summary for: {summary['date_range']}")
        print(f"Message count: {summary['message_count']}")
        print(f"Participant count: {summary['participant_count']}")
        print(f"Summary preview: {summary['summary'][:200]}...")
        
        # Check if it's a fallback summary
        if "**ACTIVITY OVERVIEW**" in summary['summary']:
            print("✅ SUCCESS: Got fallback summary with structured content")
        elif "Summary temporarily unavailable" in summary['summary']:
            print("⚠️ ISSUE: Got quota exceeded message instead of fallback")
        else:
            print("✅ Got normal AI summary")
    else:
        print("❌ No summaries generated")

if __name__ == "__main__":
    test_quota_handling()