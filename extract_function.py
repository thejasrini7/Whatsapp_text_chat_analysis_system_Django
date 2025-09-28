#!/usr/bin/env python3
"""
Extract and display the generateWeeklySummary function from the frontend file
"""

def extract_function():
    """Extract the generateWeeklySummary function"""
    file_path = "whatsapp_django/chatapp/templates/chatapp/react_dashboard.html"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the function start
        function_start_line = -1
        for i, line in enumerate(lines):
            if 'async function generateWeeklySummary()' in line:
                function_start_line = i
                break
        
        if function_start_line == -1:
            print("❌ Could not find generateWeeklySummary function")
            return
        
        print(f"Found function starting at line {function_start_line + 1}")
        
        # Find the function end (looking for the closing brace)
        function_end_line = -1
        brace_count = 0
        for i in range(function_start_line, min(function_start_line + 100, len(lines))):
            line = lines[i]
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and '}' in line:
                function_end_line = i
                break
        
        if function_end_line == -1:
            print("❌ Could not find function end")
            return
        
        print(f"Function ends at line {function_end_line + 1}")
        
        # Extract and display the function
        function_lines = lines[function_start_line:function_end_line + 1]
        function_content = ''.join(function_lines)
        
        print("\n=== Current generateWeeklySummary Function ===")
        print(function_content)
        
        # Check for our fixes
        print("\n=== Fix Status ===")
        checks = [
            ("Sorting fix", "Sort weeks by date" in function_content),
            ("Week numbering", "Week ${index + 1}:" in function_content),
            ("Quota handling", "Summary temporarily unavailable" in function_content),
            ("Proper map function", "sortedWeeks.map((week, index)" in function_content)
        ]
        
        for check_name, present in checks:
            status = "✅" if present else "❌"
            print(f"{status} {check_name}: {'Present' if present else 'Missing'}")
            
        # If fixes are missing, show what needs to be fixed
        if not all([check[1] for check in checks]):
            print("\n=== Issues Found ===")
            if not checks[0][1]:  # Sorting
                print("1. Missing sorting of weekly summaries")
            if not checks[1][1]:  # Week numbering
                print("2. Missing week numbering in display")
            if not checks[2][1]:  # Quota handling
                print("3. Missing quota exceeded message handling")
            if not checks[3][1]:  # Proper map function
                print("4. Using old map function without index parameter")
                
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    extract_function()