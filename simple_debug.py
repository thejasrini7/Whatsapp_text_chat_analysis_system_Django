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
from chatapp.utils import filter_messages_by_date
from chatapp.summary_generator import parse_timestamp

def simple_debug():
    print("=== Simple Debug of Weekly Summary Issue ===")
    
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
    
    # Now let's manually simulate what generate_weekly_summary does
    print(f"\n=== Simulating generate_weekly_summary logic ===")
    
    # Parse start and end dates
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    # Process weeks
    weekly_summaries = []
    processed_weeks = 0
    
    for week_key, week_messages in sorted(weeks.items()):
        if not week_messages:
            continue
            
        # Check if this week falls within the specified date range
        week_start = datetime.strptime(week_key, '%Y-%m-%d')
        week_end = week_start + timedelta(days=6)
        
        print(f"\nChecking week: {week_key}")
        print(f"  Week start: {week_start}")
        print(f"  Week end: {week_end}")
        print(f"  Filter start: {start_date}")
        print(f"  Filter end: {end_date}")
        
        # Skip weeks that are outside the specified date range
        if start_date and week_end < start_date:
            print(f"  SKIP: Week ends before start date")
            continue
        if end_date and week_start > end_date:
            print(f"  SKIP: Week starts after end date")
            continue
            
        print(f"  INCLUDE: Week is within date range")
        processed_weeks += 1
        
        # For debugging, let's stop after a few weeks
        if processed_weeks >= 3:
            print("  Stopping early for debugging...")
            break
    
    print(f"\nWould generate {processed_weeks} weekly summaries (stopped early for debugging)")

if __name__ == "__main__":
    simple_debug()