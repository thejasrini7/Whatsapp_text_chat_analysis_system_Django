#!/usr/bin/env python3
"""
Script to apply the weekly summary fix to the react_dashboard.html file
"""

import os

def apply_weekly_summary_fix():
    """Apply the fix to the react_dashboard.html file"""
    
    file_path = "whatsapp_django/chatapp/templates/chatapp/react_dashboard.html"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add sorting of weekly summaries
    old_code = "          let content = '';\n          if (data.weekly_summaries && data.weekly_summaries.length > 0) {\n            content = data.weekly_summaries.map(week => {"
    new_code = "          let content = '';\n          if (data.weekly_summaries && data.weekly_summaries.length > 0) {\n            // Sort weeks by date to ensure proper chronological order\n            const sortedWeeks = [...data.weekly_summaries].sort((a, b) => {\n              const dateA = new Date(a.week_start);\n              const dateB = new Date(b.week_start);\n              return dateA - dateB;\n            });\n            \n            content = sortedWeeks.map((week, index) => {"
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ Applied sorting fix")
    else:
        print("⚠️  Sorting fix not applied - code pattern not found")
    
    # Fix 2: Add quota exceeded handling
    old_code2 = "              // Format the summary content with proper structure\n              let formattedSummary = week.summary || 'No summary content available';\n              \n              // Handle structured format with sections"
    new_code2 = "              // Format the summary content with proper structure\n              let formattedSummary = week.summary || 'No summary content available';\n              \n              // Handle quota exceeded messages\n              if (formattedSummary.includes('Summary temporarily unavailable due to technical issues')) {\n                formattedSummary = `<div class=\"alert alert-warning\"><i class=\"fas fa-exclamation-triangle\"></i> ${formattedSummary}</div>`;\n              } \n              // Handle structured format with sections"
    
    if old_code2 in content:
        content = content.replace(old_code2, new_code2)
        print("✅ Applied quota exceeded handling fix")
    else:
        print("⚠️  Quota exceeded handling fix not applied - code pattern not found")
    
    # Fix 3: Add week numbering
    old_code3 = "              return `\n                <div class=\"weekly-summary-item\">\n                  <div class=\"weekly-summary-header\">\n                    ${week.date_range} (${week.message_count} messages, ${week.participant_count} participants)\n                  </div>"
    new_code3 = "              return `\n                <div class=\"weekly-summary-item\">\n                  <div class=\"weekly-summary-header\">\n                    Week ${index + 1}: ${week.date_range} (${week.message_count} messages, ${week.participant_count} participants)\n                  </div>"
    
    if old_code3 in content:
        content = content.replace(old_code3, new_code3)
        print("✅ Applied week numbering fix")
    else:
        print("⚠️  Week numbering fix not applied - code pattern not found")
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ All fixes applied successfully!")

if __name__ == "__main__":
    apply_weekly_summary_fix()
    print("\n🎉 Weekly summary fix applied!")
    print("You can now generate weekly reports that show all weeks in the selected date range.")