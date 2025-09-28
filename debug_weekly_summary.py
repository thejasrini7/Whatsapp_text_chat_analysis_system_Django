import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.utils import filter_messages_by_date
from chatapp.summary_generator import generate_weekly_summary

def debug_weekly_summary():
    # Load chat data
    chat_data = load_all_chats()
    
    # Get the first group for testing
    if not chat_data:
        print("No chat data found")
        return
        
    group_name = list(chat_data.keys())[0]
    print(f"Testing with group: {group_name}")
    
    messages = chat_data[group_name]['messages']
    print(f"Total messages: {len(messages)}")
    
    # Filter messages for a date range that should contain multiple weeks
    # Let's use a wide date range to ensure we get multiple weeks
    start_date_str = "2023-01-01"
    end_date_str = "2024-12-31"
    
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Filtered messages: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages in date range")
        return
    
    # Print date range of filtered messages
    timestamps = []
    for msg in filtered_messages:
        dt = None
        try:
            # Try to parse timestamp
            from chatapp.summary_generator import parse_timestamp
            dt = parse_timestamp(msg['timestamp'])
        except:
            pass
        if dt:
            timestamps.append(dt)
    
    if timestamps:
        print(f"Date range of filtered messages: {min(timestamps)} to {max(timestamps)}")
    
    # Generate weekly summaries
    print("Generating weekly summaries...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Print details of each week
    for i, summary in enumerate(weekly_summaries):
        print(f"\nWeek {i+1}:")
        print(f"  Week start: {summary['week_start']}")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Message count: {summary['message_count']}")
        print(f"  Participant count: {summary['participant_count']}")
        print(f"  Most active user: {summary['most_active_user']}")
        print(f"  Summary preview: {summary['summary'][:100]}...")

if __name__ == "__main__":
    debug_weekly_summary()