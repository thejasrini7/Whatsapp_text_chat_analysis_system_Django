import requests
import json

def test_actual_api():
    print("=== Testing Actual API Endpoint ===")
    
    # Test data for a small date range
    test_data = {
        "group_name": "Whatsapp Chat With Unofficial Aids C",
        "summary_type": "weekly_summary",
        "start_date": "2024-06-03",
        "end_date": "2024-06-09"
    }
    
    print(f"Sending request to http://127.0.0.1:8000/summarize/")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/summarize/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'weekly_summaries' in data:
                summaries = data['weekly_summaries']
                print(f"Number of weekly summaries: {len(summaries)}")
                
                for i, summary in enumerate(summaries):
                    print(f"\nWeek {i+1}: {summary['date_range']}")
                    print(f"  Messages: {summary['message_count']}")
                    print(f"  Participants: {summary['participant_count']}")
                    
                    # Check what type of summary we got
                    if "Summary temporarily unavailable due to technical issues" in summary['summary']:
                        print(f"  Status: QUOTA EXCEEDED MESSAGE")
                    elif "**ACTIVITY OVERVIEW**" in summary['summary']:
                        print(f"  Status: FALLBACK SUMMARY")
                    else:
                        print(f"  Status: NORMAL AI SUMMARY")
                        
                    # Show a preview of the summary
                    summary_preview = summary['summary'][:150] + "..." if len(summary['summary']) > 150 else summary['summary']
                    print(f"  Summary preview: {summary_preview}")
            else:
                print("No weekly_summaries in response")
                print(f"Full response: {data}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_api()