#!/usr/bin/env python3
"""
Debug script to investigate why only one week is displayed in the weekly summary
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

def debug_weekly_display():
    """Debug why only one week is displayed"""
    print("=== Debugging Weekly Display Issue ===")
    
    # Load chat data
    chat_data = load_all_chats()
    
    if not chat_data:
        print("❌ No chat data found")
        return
        
    # Get the first group for testing
    group_names = list(chat_data.keys())
    print(f"📊 Available groups: {group_names}")
    
    # Test with the specific date range from user's example
    start_date_str = "2024-06-03"
    end_date_str = "2024-06-09"
    
    print(f"\n🔍 Testing with specific date range: {start_date_str} to {end_date_str}")
    
    for group_name in group_names:
        print(f"\n🧪 Testing group: {group_name}")
        messages = chat_data[group_name]['messages']
        print(f"📊 Total messages in group: {len(messages)}")
        
        # Filter messages for this date range
        filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
        print(f"📅 Messages after filtering: {len(filtered_messages)}")
        
        if filtered_messages:
            # Show first few filtered messages
            print("📋 Sample filtered messages:")
            for i, msg in enumerate(filtered_messages[:5]):
                print(f"  {i+1}. {msg['timestamp']} - {msg['sender']}: {msg['message'][:50]}...")
            
            # Generate weekly summaries
            print(f"\n🔄 Generating weekly summaries...")
            weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
            print(f"✅ Generated {len(weekly_summaries)} weekly summaries")
            
            # Show details
            for i, summary in enumerate(weekly_summaries):
                print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
                print(f"    Participants: {summary['participant_count']}")
                print(f"    Summary preview: {summary['summary'][:100]}...")
            break
        else:
            print("⏭ No messages in this date range, trying next group...")
    
    # Now test with a wider date range to see if we get multiple weeks
    print(f"\n🔍 Testing with wider date range to check for multiple weeks:")
    start_date_str = "2024-06-01"
    end_date_str = "2024-06-30"
    
    for group_name in group_names:
        print(f"\n🧪 Testing group: {group_name} with wider range")
        messages = chat_data[group_name]['messages']
        
        # Filter messages for this date range
        filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
        print(f"📅 Messages after filtering: {len(filtered_messages)}")
        
        if filtered_messages:
            # Generate weekly summaries
            print(f"\n🔄 Generating weekly summaries...")
            weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
            print(f"✅ Generated {len(weekly_summaries)} weekly summaries")
            
            # Show details
            for i, summary in enumerate(weekly_summaries):
                print(f"  Week {i+1}: {summary['date_range']} - {summary['message_count']} messages")
            break

def check_frontend_code():
    """Check if the frontend fixes were properly applied"""
    print("\n=== Checking Frontend Code ===")
    
    file_path = "whatsapp_django/chatapp/templates/chatapp/react_dashboard.html"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for our fixes
        if "Sort weeks by date to ensure proper chronological order" in content:
            print("✅ Sorting fix is present")
        else:
            print("❌ Sorting fix is missing")
            
        if "Week ${index + 1}:" in content:
            print("✅ Week numbering fix is present")
        else:
            print("❌ Week numbering fix is missing")
            
        if "Summary temporarily unavailable due to technical issues" in content:
            print("✅ Quota exceeded handling fix is present")
        else:
            print("❌ Quota exceeded handling fix is missing")
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")

if __name__ == "__main__":
    debug_weekly_display()
    check_frontend_code()
    print("\n🎉 Debugging completed!")