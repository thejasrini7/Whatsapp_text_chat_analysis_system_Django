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
from chatapp.summary_generator import parse_timestamp

def debug_double_filtering():
    # Load chat data
    chat_data = load_all_chats()
    
    # Look for the specific group
    group_name = "Whatsapp Chat With Unofficial Aids C"
    if group_name not in chat_data:
        print(f"Group '{group_name}' not found!")
        return
    
    print(f"Debugging double filtering for group: {group_name}")
    
    # Get messages
    messages = chat_data[group_name]['messages']
    print(f"Total messages in group: {len(messages)}")
    
    # Test with July 2024 date range
    start_date_str = "2024-07-01"
    end_date_str = "2024-07-31"
    
    print(f"\nFirst filtering (views.py): {start_date_str} to {end_date_str}")
    
    # First filtering (as done in views.py)
    filtered_messages_1 = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"Messages after first filtering: {len(filtered_messages_1)}")
    
    # Show sample messages after first filtering
    if filtered_messages_1:
        print("\nSample messages after first filtering:")
        for i, msg in enumerate(filtered_messages_1[:3]):
            dt = parse_timestamp(msg['timestamp'])
            print(f"  {i+1}. {msg['timestamp']} ({dt}) - {msg['sender']}: {msg['message'][:50]}...")
    
    # Second filtering (as done in generate_weekly_summary)
    print(f"\nSecond filtering (generate_weekly_summary): {start_date_str} to {end_date_str}")
    
    filter_start_date = None
    filter_end_date = None
    if start_date_str:
        filter_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    if end_date_str:
        filter_end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        filter_end_date = filter_end_date.replace(hour=23, minute=59, second=59)
    
    print(f"Filter dates: start={filter_start_date}, end={filter_end_date}")
    
    filtered_messages_2 = []
    for msg in filtered_messages_1:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
        
        # If date filtering is active, check if message is within range
        if filter_start_date and dt < filter_start_date:
            print(f"  Excluding message (too early): {msg['timestamp']} ({dt})")
            continue
        if filter_end_date and dt > filter_end_date:
            print(f"  Excluding message (too late): {msg['timestamp']} ({dt})")
            continue
            
        filtered_messages_2.append(msg)
    
    print(f"Messages after second filtering: {len(filtered_messages_2)}")
    
    # Show sample messages after second filtering
    if filtered_messages_2:
        print("\nSample messages after second filtering:")
        for i, msg in enumerate(filtered_messages_2[:3]):
            dt = parse_timestamp(msg['timestamp'])
            print(f"  {i+1}. {msg['timestamp']} ({dt}) - {msg['sender']}: {msg['message'][:50]}...")

if __name__ == "__main__":
    debug_double_filtering()