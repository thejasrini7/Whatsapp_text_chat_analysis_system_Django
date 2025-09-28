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
from chatapp.summary_generator import generate_weekly_summary

def test_date_range_issue():
    print("=== Testing Date Range Issue ===")
    
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
    
    # Test with the exact date range from user's report
    start_date_str = "2023-09-20"
    end_date_str = "2025-09-23"
    
    print(f"\nFiltering messages for date range: {start_date_str} to {end_date_str}")
    
    # Use the same filtering logic as in views.py
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after filtering: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages found after filtering!")
        return
    
    # Generate weekly summaries
    print(f"\nGenerating weekly summaries...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Show the first few and last few weeks to verify we have the full range
    print(f"\n=== First 3 Weeks ===")
    for i in range(min(3, len(weekly_summaries))):
        summary = weekly_summaries[i]
        print(f"Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
        if "Summary temporarily unavailable" in summary['summary']:
            print(f"  ⚠️  Quota exceeded - using fallback")
        else:
            print(f"  ✅ Has summary content")
    
    print(f"\n=== Last 3 Weeks ===")
    for i in range(max(0, len(weekly_summaries)-3), len(weekly_summaries)):
        summary = weekly_summaries[i]
        print(f"Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
        if "Summary temporarily unavailable" in summary['summary']:
            print(f"  ⚠️  Quota exceeded - using fallback")
        else:
            print(f"  ✅ Has summary content")
    
    # Check for the specific week mentioned by the user
    user_week_found = False
    for i, summary in enumerate(weekly_summaries):
        if "03 Jun 2024 to 09 Jun 2024" in summary['date_range']:
            print(f"\n=== User's Reported Week (Week {i+1}) ===")
            print(f"Date range: {summary['date_range']}")
            print(f"Message count: {summary['message_count']}")
            print(f"Participant count: {summary['participant_count']}")
            print(f"Summary preview: {summary['summary'][:200]}...")
            user_week_found = True
            break
    
    if not user_week_found:
        print(f"\n⚠️  User's reported week (03 Jun 2024 to 09 Jun 2024) not found in results!")
    
    # Check how many weeks show quota exceeded vs fallback content
    quota_exceeded_count = 0
    fallback_count = 0
    normal_count = 0
    
    for summary in weekly_summaries:
        if "Summary temporarily unavailable" in summary['summary']:
            quota_exceeded_count += 1
        elif "**ACTIVITY OVERVIEW**" in summary['summary'] or "**MAIN DISCUSSION TOPICS**" in summary['summary']:
            fallback_count += 1
        else:
            normal_count += 1
    
    print(f"\n=== Summary Statistics ===")
    print(f"Total weeks: {len(weekly_summaries)}")
    print(f"Weeks with quota exceeded message: {quota_exceeded_count}")
    print(f"Weeks with fallback summaries: {fallback_count}")
    print(f"Weeks with normal AI summaries: {normal_count}")

if __name__ == "__main__":
    test_date_range_issue()