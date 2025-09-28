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

def debug_detailed_filtering():
    # Load chat data
    chat_data = load_all_chats()
    
    # Look for the specific group
    group_name = "Whatsapp Chat With Unofficial Aids C"
    if group_name not in chat_data:
        print(f"Group '{group_name}' not found!")
        return
    
    print(f"Debugging detailed filtering for group: {group_name}")
    
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
    message_dates = []
    
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
        
        # Collect all parsed dates for debugging
        message_dates.append(dt)
        
        # If date filtering is active, check if message is within range
        if filter_start_date and dt < filter_start_date:
            continue
        if filter_end_date and dt > filter_end_date:
            continue
            
        filtered_messages.append(msg)
    
    print(f"Messages after date filtering: {len(filtered_messages)}")
    
    # Show date range of filtered messages
    if message_dates:
        print(f"Full date range of all messages: {min(message_dates)} to {max(message_dates)}")
    
    if filtered_messages:
        filtered_dates = []
        for msg in filtered_messages:
            dt = parse_timestamp(msg['timestamp'])
            if dt:
                filtered_dates.append(dt)
        
        if filtered_dates:
            print(f"Date range of filtered messages: {min(filtered_dates)} to {max(filtered_dates)}")
    
    # Show all filtered messages with their dates
    print(f"\nAll filtered messages:")
    for i, msg in enumerate(filtered_messages):
        dt = parse_timestamp(msg['timestamp'])
        print(f"  {i+1:3d}. {msg['timestamp']} ({dt}) - {msg['sender']}: {msg['message'][:50]}...")
        
        # Stop after showing a reasonable number
        if i >= 50:
            print(f"  ... and {len(filtered_messages) - 51} more messages")
            break

if __name__ == "__main__":
    debug_detailed_filtering()