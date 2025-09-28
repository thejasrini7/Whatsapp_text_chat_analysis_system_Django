#!/usr/bin/env python3
"""
Test the specific date range mentioned by the user:
Starts from 20 / 09 / 2023
To 23 / 09 / 2025
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.utils import filter_messages_by_date
from chatapp.summary_generator import generate_weekly_summary

def test_user_date_range():
    """Test the specific date range mentioned by the user"""
    print("=== Testing User's Date Range ===")
    print("Starts from 20 / 09 / 2023")
    print("To 23 / 09 / 2025")
    
    # Convert to the format used by the system
    start_date_str = "2023-09-20"
    end_date_str = "2025-09-23"
    
    print(f"Converted to system format: {start_date_str} to {end_date_str}")
    
    # Load chat data
    chat_data = load_all_chats()
    
    if not chat_data:
        print("❌ No chat data found")
        return
        
    # Test with the first group
    group_name = list(chat_data.keys())[0]
    print(f"\n🧪 Testing group: {group_name}")
    
    messages = chat_data[group_name]['messages']
    print(f"📊 Total messages in group: {len(messages)}")
    
    # Filter messages for this date range
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    print(f"📅 Messages after filtering: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("❌ No messages found in this date range")
        return
    
    # Show date range of filtered messages
    timestamps = []
    for msg in filtered_messages:
        try:
            from chatapp.summary_generator import parse_timestamp
            dt = parse_timestamp(msg['timestamp'])
            if dt:
                timestamps.append(dt)
        except:
            pass
    
    if timestamps:
        print(f"📆 Date range of filtered messages: {min(timestamps).strftime('%d %b %Y')} to {max(timestamps).strftime('%d %b %Y')}")
    
    # Generate weekly summaries
    print(f"\n🔄 Generating weekly summaries...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"✅ Generated {len(weekly_summaries)} weekly summaries")
    
    # Show first few and last few weeks
    print(f"\n⏮ First 5 weeks:")
    for i in range(min(5, len(weekly_summaries))):
        summary = weekly_summaries[i]
        print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
    
    if len(weekly_summaries) > 5:
        print(f"\n⏭ Last 5 weeks:")
        for i in range(max(0, len(weekly_summaries)-5), len(weekly_summaries)):
            summary = weekly_summaries[i]
            print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")

def check_frontend_response_handling():
    """Check how the frontend handles the response"""
    print("\n=== Checking Frontend Response Handling ===")
    
    # Simulate what the backend would return for multiple weeks
    sample_response = {
        "summary_type": "weekly_summary",
        "weekly_summaries": [
            {
                "week_start": "2023-09-18",
                "date_range": "18 Sep 2023 to 24 Sep 2023",
                "summary": "**ACTIVITY OVERVIEW**: 15 messages from 3 participants during this week",
                "message_count": 15,
                "participant_count": 3,
                "most_active_user": "User A"
            },
            {
                "week_start": "2023-09-25",
                "date_range": "25 Sep 2023 to 01 Oct 2023",
                "summary": "**ACTIVITY OVERVIEW**: 8 messages from 2 participants during this week",
                "message_count": 8,
                "participant_count": 2,
                "most_active_user": "User B"
            },
            {
                "week_start": "2023-10-02",
                "date_range": "02 Oct 2023 to 08 Oct 2023",
                "summary": "Summary temporarily unavailable due to technical issues.",
                "message_count": 12,
                "participant_count": 4,
                "most_active_user": "User C"
            }
        ]
    }
    
    print("Sample backend response with 3 weeks:")
    print(f"Number of weekly summaries: {len(sample_response['weekly_summaries'])}")
    
    # Check if our frontend code would handle this correctly
    file_path = "whatsapp_django/chatapp/templates/chatapp/react_dashboard.html"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the key parts of our fix are in place
        checks = [
            ("Sorting fix", "Sort weeks by date to ensure proper chronological order" in content),
            ("Week numbering", "Week ${index + 1}:" in content),
            ("Quota handling", "Summary temporarily unavailable due to technical issues" in content)
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {'Present' if passed else 'Missing'}")
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")

if __name__ == "__main__":
    test_user_date_range()
    check_frontend_response_handling()
    print("\n🎉 User date range test completed!")