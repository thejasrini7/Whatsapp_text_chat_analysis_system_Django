import os
import sys
import django
import json
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import load_all_chats
from chatapp.utils import filter_messages_by_date
from chatapp.summary_generator import generate_weekly_summary

def test_api_simulation():
    print("=== Simulating API Call Exactly ===")
    
    # Test data matching what the user reported
    test_data = {
        "group_name": "Whatsapp Chat With Unofficial Aids C",
        "summary_type": "weekly_summary",
        "start_date": "2023-09-20",
        "end_date": "2025-09-23"
    }
    
    print(f"Simulating request with data: {json.dumps(test_data, indent=2)}")
    
    # Replicate exactly what the API endpoint does
    group_name = test_data.get('group_name')
    summary_type = test_data.get('summary_type', 'total')
    start_date_str = test_data.get('start_date')
    end_date_str = test_data.get('end_date')
    user = test_data.get('user')
    
    if not group_name:
        print("Invalid group name")
        return
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        print("Group not found")
        return
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    print(f"Filtered messages: {len(filtered_messages)}")
    
    if not filtered_messages:
        print("No messages found in the selected date range")
        return
    
    if summary_type == 'weekly_summary':
        print("Calling generate_weekly_summary...")
        weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
        print(f"Generated {len(weekly_summaries)} weekly summaries")
        
        # Analyze results like the API would
        quota_exceeded_count = 0
        fallback_count = 0
        normal_count = 0
        
        print("\nAnalyzing first 5 and last 5 summaries:")
        
        # Check first few
        for i in range(min(5, len(weekly_summaries))):
            summary = weekly_summaries[i]
            print(f"\nWeek {i+1}: {summary['date_range']}")
            
            if "Summary temporarily unavailable due to technical issues" in summary['summary']:
                print(f"  Status: QUOTA EXCEEDED MESSAGE")
                quota_exceeded_count += 1
            elif "**ACTIVITY OVERVIEW**" in summary['summary']:
                print(f"  Status: FALLBACK SUMMARY")
                fallback_count += 1
            else:
                print(f"  Status: NORMAL AI SUMMARY")
                normal_count += 1
                
            # Show a preview of the summary (first 100 chars)
            summary_preview = summary['summary'][:100] + "..." if len(summary['summary']) > 100 else summary['summary']
            print(f"  Summary preview: {summary_preview}")
        
        # Check last few if we have more than 10
        if len(weekly_summaries) > 10:
            print("\n... (skipping middle weeks) ...")
            for i in range(max(len(weekly_summaries)-5, 5), len(weekly_summaries)):
                summary = weekly_summaries[i]
                print(f"\nWeek {i+1}: {summary['date_range']}")
                
                if "Summary temporarily unavailable due to technical issues" in summary['summary']:
                    print(f"  Status: QUOTA EXCEEDED MESSAGE")
                    quota_exceeded_count += 1
                elif "**ACTIVITY OVERVIEW**" in summary['summary']:
                    print(f"  Status: FALLBACK SUMMARY")
                    fallback_count += 1
                else:
                    print(f"  Status: NORMAL AI SUMMARY")
                    normal_count += 1
                    
                # Show a preview of the summary (first 100 chars)
                summary_preview = summary['summary'][:100] + "..." if len(summary['summary']) > 100 else summary['summary']
                print(f"  Summary preview: {summary_preview}")
        
        print(f"\n=== FINAL SUMMARY STATISTICS ===")
        print(f"Total weeks: {len(weekly_summaries)}")
        print(f"Weeks with quota exceeded messages: {quota_exceeded_count}")
        print(f"Weeks with fallback summaries: {fallback_count}")
        print(f"Weeks with normal AI summaries: {normal_count}")
        
        if quota_exceeded_count > 0:
            print(f"\n❌ ISSUE: {quota_exceeded_count} weeks showing quota exceeded instead of fallback summaries")
            print("This suggests the fallback mechanism isn't working properly in the API context")
        else:
            print(f"\n✅ SUCCESS: All weeks have proper fallback or normal summaries")

if __name__ == "__main__":
    test_api_simulation()