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

def test_multiple_weeks_quota():
    print("=== Testing Multiple Weeks with Quota Exceeded ===")
    
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
    
    # Test with a small date range that should contain multiple weeks
    start_date_str = "2024-06-01"
    end_date_str = "2024-06-30"
    
    print(f"\nFiltering messages for date range: {start_date_str} to {end_date_str}")
    
    # Use the same filtering logic as in views.py
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after filtering: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages found after filtering!")
        return
    
    # Generate weekly summaries - this should trigger multiple API calls
    print(f"\nGenerating weekly summaries (this may take a while and show quota errors)...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Analyze the results
    quota_exceeded_count = 0
    fallback_count = 0
    normal_count = 0
    
    for i, summary in enumerate(weekly_summaries):
        print(f"\nWeek {i+1}: {summary['date_range']}")
        print(f"  Messages: {summary['message_count']}")
        print(f"  Participants: {summary['participant_count']}")
        
        if "Summary temporarily unavailable due to technical issues" in summary['summary']:
            print(f"  Status: QUOTA EXCEEDED MESSAGE")
            quota_exceeded_count += 1
        elif "**ACTIVITY OVERVIEW**" in summary['summary']:
            print(f"  Status: FALLBACK SUMMARY")
            fallback_count += 1
        else:
            print(f"  Status: NORMAL AI SUMMARY")
            normal_count += 1
            
        # Show a preview of the summary
        summary_preview = summary['summary'][:150] + "..." if len(summary['summary']) > 150 else summary['summary']
        print(f"  Summary preview: {summary_preview}")
    
    print(f"\n=== SUMMARY STATISTICS ===")
    print(f"Total weeks: {len(weekly_summaries)}")
    print(f"Weeks with quota exceeded messages: {quota_exceeded_count}")
    print(f"Weeks with fallback summaries: {fallback_count}")
    print(f"Weeks with normal AI summaries: {normal_count}")
    
    if quota_exceeded_count > 0:
        print(f"\n❌ ISSUE: {quota_exceeded_count} weeks showing quota exceeded instead of fallback summaries")
        print("This suggests the fallback mechanism isn't working properly in the API context")
    else:
        print(f"\n✅ SUCCESS: All weeks have proper fallback or normal summaries")

if __name__ == "__main__":
    test_multiple_weeks_quota()