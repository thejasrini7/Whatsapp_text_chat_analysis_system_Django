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

import requests

def test_api_direct():
    print("=== Testing Weekly Summary API Directly ===")
    
    # Test data matching what the user reported
    test_data = {
        "group_name": "Whatsapp Chat With Unofficial Aids C",
        "summary_type": "weekly_summary",
        "start_date": "2023-09-20",
        "end_date": "2025-09-23"
    }
    
    print(f"Sending request with data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make a direct request to the API
        response = requests.post(
            'http://localhost:8000/summarize/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data keys: {list(data.keys())}")
            
            if 'weekly_summaries' in data:
                summaries = data['weekly_summaries']
                print(f"Number of weekly summaries: {len(summaries)}")
                
                if len(summaries) > 0:
                    print("\nFirst 3 summaries:")
                    for i, summary in enumerate(summaries[:3]):
                        print(f"  Week {i+1}:")
                        print(f"    Date range: {summary.get('date_range', 'N/A')}")
                        print(f"    Message count: {summary.get('message_count', 'N/A')}")
                        print(f"    Participant count: {summary.get('participant_count', 'N/A')}")
                        print(f"    Summary preview: {summary.get('summary', '')[:100]}...")
                        
                    print("\nLast 3 summaries:")
                    for i, summary in enumerate(summaries[-3:], len(summaries)-2):
                        print(f"  Week {i}:")
                        print(f"    Date range: {summary.get('date_range', 'N/A')}")
                        print(f"    Message count: {summary.get('message_count', 'N/A')}")
                        print(f"    Participant count: {summary.get('participant_count', 'N/A')}")
                        print(f"    Summary preview: {summary.get('summary', '')[:100]}...")
                else:
                    print("No weekly summaries returned")
            else:
                print("No 'weekly_summaries' key in response")
                print(f"Response data: {data}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_direct()