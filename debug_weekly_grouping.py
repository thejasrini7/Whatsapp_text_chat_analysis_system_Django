import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.summary_generator import parse_timestamp

def debug_weekly_grouping():
    # Load chat data
    chat_data = load_all_chats()
    
    # Look for the specific group
    group_name = "Whatsapp Chat With Unofficial Aids C"
    if group_name not in chat_data:
        print(f"Group '{group_name}' not found!")
        return
    
    print(f"Debugging weekly grouping for group: {group_name}")
    
    # Get messages
    messages = chat_data[group_name]['messages']
    print(f"Total messages in group: {len(messages)}")
    
    # Test with July 2024 date range
    start_date_str = "2024-07-01"
    end_date_str = "2024-07-31"
    
    filter_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    filter_end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    filter_end_date = filter_end_date.replace(hour=23, minute=59, second=59)
    
    print(f"\nFiltering for date range: {filter_start_date} to {filter_end_date}")
    
    # Filter messages by date range (same logic as in generate_weekly_summary)
    filtered_messages = []
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
        
        # If date filtering is active, check if message is within range
        if filter_start_date and dt < filter_start_date:
            continue
        if filter_end_date and dt > filter_end_date:
            continue
            
        filtered_messages.append(msg)
    
    print(f"Messages after date filtering: {len(filtered_messages)}")
    
    # Show some sample filtered messages
    if filtered_messages:
        print("\nSample filtered messages:")
        for i, msg in enumerate(filtered_messages[:5]):
            print(f"  {i+1}. {msg['timestamp']} - {msg['sender']}: {msg['message'][:50]}...")
    
    # Group filtered messages by week (same logic as in generate_weekly_summary)
    weeks = {}
    for msg in filtered_messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
            
        monday = dt - timedelta(days=dt.weekday())
        week_key = monday.strftime('%Y-%m-%d')
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(msg)
    
    print(f"\nNumber of weeks with messages: {len(weeks)}")
    
    # Show details for each week
    for week_key, week_messages in sorted(weeks.items()):
        monday = datetime.strptime(week_key, '%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        date_range = f"{monday.strftime('%d %b %Y')} to {sunday.strftime('%d %b %Y')}" 
        
        print(f"\nWeek starting {week_key} ({date_range}):")
        print(f"  Messages: {len(week_messages)}")
        
        # Show unique senders
        senders = set(msg['sender'] for msg in week_messages)
        print(f"  Senders: {len(senders)} - {list(senders)[:5]}")
        
        # Show sample messages
        if week_messages:
            print("  Sample messages:")
            for i, msg in enumerate(week_messages[:3]):
                print(f"    {msg['timestamp']} - {msg['sender']}: {msg['message'][:50]}...")

if __name__ == "__main__":
    debug_weekly_grouping()