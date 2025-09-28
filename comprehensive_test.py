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

def comprehensive_test():
    print("=== Comprehensive Test for Weekly Summary Fix ===")
    
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
    start_date_str = "2024-06-01"
    end_date_str = "2024-09-30"
    
    print(f"\nFiltering messages for date range: {start_date_str} to {end_date_str}")
    
    # Use the same filtering logic as in views.py
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after filtering: {len(filtered_messages)}")
    
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
    
    # Verify that we're getting multiple weeks
    if len(weekly_summaries) > 1:
        print(f"\n✅ SUCCESS: Generated {len(weekly_summaries)} weeks instead of just 1!")
        print("✅ The main issue has been fixed - multiple weeks are now displayed")
    else:
        print(f"\n❌ ISSUE: Still only generating {len(weekly_summaries)} week")
        
    # Check if we're getting proper message counts
    total_messages_in_weeks = sum(summary['message_count'] for summary in weekly_summaries)
    if total_messages_in_weeks > 10:
        print(f"✅ SUCCESS: Total messages in weeks: {total_messages_in_weeks} (proper message counts)")
    else:
        print(f"⚠️  NOTE: Total messages in weeks: {total_messages_in_weeks} (may be affected by date parsing)")
        
    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    comprehensive_test()