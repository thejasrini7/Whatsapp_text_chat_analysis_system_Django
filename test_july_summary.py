import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.summary_generator import generate_weekly_summary

def test_july_summary():
    # Load chat data
    chat_data = load_all_chats()
    
    # Look for the specific group
    group_name = "Whatsapp Chat With Unofficial Aids C"
    if group_name not in chat_data:
        print(f"Group '{group_name}' not found!")
        return
    
    print(f"Testing weekly summary for group: {group_name}")
    
    # Get messages
    messages = chat_data[group_name]['messages']
    print(f"Total messages: {len(messages)}")
    
    # Test with July 2024 date range
    start_date = "2024-07-01"
    end_date = "2024-07-31"
    
    print(f"\nGenerating weekly summary for {start_date} to {end_date}")
    
    weekly_summaries = generate_weekly_summary(messages, start_date, end_date)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    for i, summary in enumerate(weekly_summaries):
        print(f"\nWeek {i+1}:")
        print(f"  Week start: {summary['week_start']}")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Messages: {summary['message_count']}")
        print(f"  Participants: {summary['participant_count']}")
        if summary['most_active_user']:
            print(f"  Most active user: {summary['most_active_user']}")
        print(f"  Summary: {summary['summary'][:100]}...")

if __name__ == "__main__":
    test_july_summary()