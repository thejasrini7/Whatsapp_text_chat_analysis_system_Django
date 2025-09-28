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

def final_verification():
    print("=== Final Verification of Weekly Summary Fix ===")
    
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
    
    # Generate weekly summaries
    print(f"\nGenerating weekly summaries...")
    weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
    print(f"Generated {len(weekly_summaries)} weekly summaries")
    
    # Verify we have multiple weeks
    if len(weekly_summaries) <= 1:
        print("❌ ISSUE: Only one week generated!")
        return
    else:
        print(f"✅ SUCCESS: Generated {len(weekly_summaries)} weeks")
    
    # Check that we have proper fallback summaries
    fallback_count = 0
    quota_exceeded_count = 0
    
    for summary in weekly_summaries:
        if "Summary temporarily unavailable due to technical issues" in summary['summary']:
            quota_exceeded_count += 1
        elif "**ACTIVITY OVERVIEW**" in summary['summary']:
            fallback_count += 1
    
    print(f"\nSummary Content Analysis:")
    print(f"  Weeks with fallback summaries: {fallback_count}")
    print(f"  Weeks with quota exceeded messages: {quota_exceeded_count}")
    print(f"  Weeks with normal AI summaries: {len(weekly_summaries) - fallback_count - quota_exceeded_count}")
    
    if fallback_count > 0:
        print("✅ SUCCESS: Fallback summaries are working correctly")
    else:
        print("⚠️  WARNING: No fallback summaries found")
    
    # Check the specific week mentioned by the user
    user_week_found = False
    for i, summary in enumerate(weekly_summaries):
        if "03 Jun 2024 to 09 Jun 2024" in summary['date_range']:
            print(f"\n✅ User's reported week found:")
            print(f"  Week {i+1}: {summary['date_range']}")
            print(f"  Messages: {summary['message_count']}")
            print(f"  Participants: {summary['participant_count']}")
            if summary['most_active_user']:
                print(f"  Most active user: {summary['most_active_user']}")
            
            # Show summary preview
            summary_preview = summary['summary'][:300] + "..." if len(summary['summary']) > 300 else summary['summary']
            print(f"  Summary preview: {summary_preview}")
            
            user_week_found = True
            break
    
    if not user_week_found:
        print("❌ ISSUE: User's reported week not found!")
    
    # Show date range coverage
    if weekly_summaries:
        first_week = weekly_summaries[0]
        last_week = weekly_summaries[-1]
        print(f"\n📅 Date Range Coverage:")
        print(f"  First week: {first_week['date_range']}")
        print(f"  Last week: {last_week['date_range']}")
        print(f"  Total weeks: {len(weekly_summaries)}")
    
    print(f"\n🎉 VERIFICATION COMPLETE")
    if len(weekly_summaries) > 1 and fallback_count > 0:
        print("✅ ALL FIXES ARE WORKING CORRECTLY!")
        print("✅ Users should now see multiple weeks with fallback summaries")
    else:
        print("⚠️  Some issues may still exist")

if __name__ == "__main__":
    final_verification()