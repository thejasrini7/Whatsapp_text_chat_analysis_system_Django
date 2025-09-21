#!/usr/bin/env python
"""
Simple test script to verify activity analysis functionality
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from chatapp.views import activity_analysis
from django.test import RequestFactory
import json

def test_activity_analysis():
    """Test the activity analysis endpoint"""
    print("Testing activity analysis...")
    
    # Create a mock request
    factory = RequestFactory()
    
    # Test data
    test_data = {
        'group_name': 'Test Group',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'include_messages': False
    }
    
    # Create request
    request = factory.post('/activity_analysis/', 
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    try:
        # Call the view
        response = activity_analysis(request)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.content)
            print("✅ Activity analysis test passed!")
            print(f"Response keys: {list(data.keys())}")
        else:
            print(f"❌ Activity analysis test failed with status {response.status_code}")
            print(f"Response: {response.content}")
            
    except Exception as e:
        print(f"❌ Activity analysis test failed with exception: {e}")

if __name__ == "__main__":
    test_activity_analysis()
