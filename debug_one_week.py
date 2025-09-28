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

def debug_one_week_issue():
    print("=== Debugging One Week Issue ===")
    
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
    
    # Let's manually check what weeks we have in the data
    print("\nAnalyzing weeks in filtered data...")
    weeks = {}
    from chatapp.summary_generator import parse_timestamp
    from datetime import timedelta
    
    for msg in filtered_messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
            
        monday = dt - timedelta(days=dt.weekday())
        week_key = monday.strftime('%Y-%m-%d')
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(msg)
    
    print(f"Total unique weeks found: {len(weeks)}")
    
    # Show first 5 and last 5 weeks
    sorted_weeks = sorted(weeks.items())
    print("\nFirst 5 weeks:")
    for i, (week_key, week_messages) in enumerate(sorted_weeks[:5]):
        monday = datetime.strptime(week_key, '%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        date_range = f"{monday.strftime('%d %b %Y')} to {sunday.strftime('%d %b %Y')}"
        print(f"  Week {i+1}: {date_range} - {len(week_messages)} messages")
    
    print("\nLast 5 weeks:")
    for i, (week_key, week_messages) in enumerate(sorted_weeks[-5:], len(sorted_weeks)-4):
        monday = datetime.strptime(week_key, '%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        date_range = f"{monday.strftime('%d %b %Y')} to {sunday.strftime('%d %b %Y')}"
        print(f"  Week {i}: {date_range} - {len(week_messages)} messages")
    
    # Now test the actual generate_weekly_summary function
    print(f"\n=== Testing generate_weekly_summary function ===")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Check if we're only getting one week
    if len(weekly_summaries) == 1:
        print("❌ ISSUE CONFIRMED: Only one week generated!")
        summary = weekly_summaries[0]
        print(f"  Week: {summary['date_range']}")
        print(f"  Messages: {summary['message_count']}")
        print(f"  Summary: {summary['summary'][:100]}...")
    else:
        print(f"✅ Multiple weeks generated: {len(weekly_summaries)}")
        # Show first 3 and last 3
        print("\nFirst 3 weeks:")
        for i in range(min(3, len(weekly_summaries))):
            summary = weekly_summaries[i]
            print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
        
        print("\nLast 3 weeks:")
        for i in range(max(0, len(weekly_summaries)-3), len(weekly_summaries)):
            summary = weekly_summaries[i]
            print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")

if __name__ == "__main__":
    debug_one_week_issue()