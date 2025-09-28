#!/usr/bin/env python3
"""
Simulate the frontend JavaScript code to see what's happening with weekly summary display
"""

import json
import re

def simulate_frontend_processing():
    """Simulate the frontend JavaScript processing"""
    print("=== Simulating Frontend JavaScript Processing ===")
    
    # Sample data that would be returned from the backend
    sample_data = {
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
    
    print(f"Backend returned {len(sample_data['weekly_summaries'])} weekly summaries")
    
    # This is the code that should be in the frontend
    content = ''
    if sample_data['weekly_summaries'] and len(sample_data['weekly_summaries']) > 0:
        # Sort weeks by date to ensure proper chronological order
        sorted_weeks = sorted(sample_data['weekly_summaries'], key=lambda x: x['week_start'])
        
        print(f"Sorted weeks: {len(sorted_weeks)}")
        
        # Simulate the map function
        content_parts = []
        for index, week in enumerate(sorted_weeks):
            # Format the summary content with proper structure
            formatted_summary = week.get('summary', 'No summary content available')
            
            # Handle quota exceeded messages
            if 'Summary temporarily unavailable due to technical issues' in formatted_summary:
                formatted_summary = f'<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> {formatted_summary}</div>'
            # Handle structured format with sections (fallback summaries and normal AI summaries)
            elif '**ACTIVITY OVERVIEW**' in formatted_summary or '**MAIN DISCUSSION TOPICS**' in formatted_summary:
                # Format structured sections
                formatted_summary = re.sub(r'\*\*([^*]+)\*\*:', r'<h4 style="color: var(--primary); margin: 1rem 0 0.5rem 0; font-weight: 600;">\1</h4>', formatted_summary)
                formatted_summary = re.sub(r'\*\*([^*]+)\*\*', r'<strong style="color: var(--primary);">\1</strong>', formatted_summary)
                formatted_summary = formatted_summary.replace('\n', '<br>')
            else:
                # Convert bullet points to proper HTML list
                if '*' in formatted_summary:
                    lines = formatted_summary.split('\n')
                    bullet_points = [line.replace('*', '', 1).strip() for line in lines if line.strip().startswith('*')]
                    bullet_points = [point for point in bullet_points if len(point) > 0]
                    
                    if len(bullet_points) > 0:
                        formatted_summary = '<ul>' + ''.join([f'<li>{point}</li>' for point in bullet_points]) + '</ul>'
            
            content_part = f'''
                <div class="weekly-summary-item">
                    <div class="weekly-summary-header">
                        Week {index + 1}: {week['date_range']} ({week['message_count']} messages, {week['participant_count']} participants)
                    </div>
                    <div class="weekly-summary-content">{formatted_summary}</div>
                </div>
            '''
            content_parts.append(content_part)
        
        content = ''.join(content_parts)
        print(f"Generated content with {len(sorted_weeks)} weeks")
    else:
        content = '<div class="alert alert-info"><i class="fas fa-info-circle"></i> No weekly summaries available for the selected date range.</div>'
    
    print(f"Final content length: {len(content)}")
    weekly_item_count = content.count('weekly-summary-item')
    print(f"Number of weekly-summary-item divs: {weekly_item_count}")
    
    # Check if all weeks are being displayed
    if weekly_item_count == len(sample_data['weekly_summaries']):
        print("✅ All weeks are being displayed correctly")
    else:
        print("❌ Not all weeks are being displayed")
    
    return content

def check_actual_frontend_code():
    """Check the actual frontend code"""
    print("\n=== Checking Actual Frontend Code ===")
    
    file_path = "whatsapp_django/chatapp/templates/chatapp/react_dashboard.html"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the generateWeeklySummary function
        function_start = content.find('async function generateWeeklySummary()')
        if function_start != -1:
            function_end = content.find('      }', function_start) + 7
            function_code = content[function_start:function_end]
            
            print(f"Found generateWeeklySummary function")
            print(f"Function length: {len(function_code)}")
            
            # Check for key components
            checks = [
                {"name": "Sorting", "present": "Sort weeks by date" in function_code},
                {"name": "Week numbering", "present": "Week ${index + 1}:" in function_code},
                {"name": "Quota handling", "present": "Summary temporarily unavailable" in function_code}
            ]
            
            for check in checks:
                status = "✅" if check["present"] else "❌"
                print(f"{status} {check['name']}: {'Present' if check['present'] else 'Missing'}")
                
            # Check if there might be an issue with the map function
            if "content = sortedWeeks.map((week, index) => {" in function_code:
                print("✅ Using correct map function with index")
            elif "content = data.weekly_summaries.map(week => {" in function_code:
                print("❌ Using old map function without index - this could be the issue!")
            else:
                print("? Map function structure unclear")
                
        else:
            print("❌ Could not find generateWeeklySummary function")
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")

if __name__ == "__main__":
    content = simulate_frontend_processing()
    check_actual_frontend_code()
    print("\n🎉 Frontend simulation completed!")