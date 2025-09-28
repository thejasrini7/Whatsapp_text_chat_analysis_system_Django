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

def debug_api_quota_issue():
    print("=== Debugging API Quota Issue ===")
    
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
    
    # Test with a date range that should contain multiple weeks
    start_date_str = "2023-09-20"
    end_date_str = "2025-09-23"
    
    print(f"\nFiltering messages for date range: {start_date_str} to {end_date_str}")
    
    # Use the same filtering logic as in views.py
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after filtering: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages found after filtering!")
        return
    
    # Test the generate_with_gemini function directly to see what error we get
    print("\nTesting direct API call...")
    test_prompt = "Say hello"
    response = generate_with_gemini(test_prompt)
    print(f"Direct API response: {response}")
    
    # Generate weekly summaries
    print(f"\nGenerating weekly summaries...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Show details for each week
    print(f"\n=== Results ===")
    for i, summary in enumerate(weekly_summaries):
        print(f"\nWeek {i+1}:")
        print(f"  Week start: {summary['week_start']}")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Message count: {summary['message_count']}")
        print(f"  Participant count: {summary['participant_count']}")
        print(f"  Most active user: {summary['most_active_user']}")
        print(f"  Summary preview: {summary['summary'][:100]}...")
        if "Summary temporarily unavailable" in summary['summary']:
            print(f"  ⚠️  This week shows quota exceeded message")
    
    # Check if we're getting proper message counts
    total_messages_in_summaries = sum(summary['message_count'] for summary in weekly_summaries)
    print(f"\nTotal messages in all summaries: {total_messages_in_summaries}")
    print(f"Filtered messages count: {len(filtered_messages)}")

if __name__ == "__main__":
    debug_api_quota_issue()