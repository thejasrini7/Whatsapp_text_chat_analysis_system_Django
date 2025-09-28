from datetime import datetime, timedelta

def test_date_filtering():
    # Test the date filtering logic
    # Simulate the user's date range: 20/09/2023 to 23/09/2025
    start_date_str = "2023-09-20"
    end_date_str = "2025-09-23"
    
    # Parse start and end dates
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    print(f"Selected date range: {start_date_str} to {end_date_str}")
    print(f"Parsed start date: {start_date}")
    print(f"Parsed end date: {end_date}")
    
    # Test some sample weeks
    sample_weeks = [
        "2024-06-03",  # 03 Jun 2024 to 09 Jun 2024
        "2023-09-18",  # 18 Sep 2023 to 24 Sep 2023
        "2025-09-22",  # 22 Sep 2025 to 28 Sep 2025
        "2022-01-01",  # 01 Jan 2022 to 07 Jan 2022 (outside range)
        "2026-01-01",  # 01 Jan 2026 to 07 Jan 2026 (outside range)
    ]
    
    print("\nTesting week filtering:")
    for week_key in sample_weeks:
        week_start = datetime.strptime(week_key, '%Y-%m-%d')
        week_end = week_start + timedelta(days=6)
        
        print(f"\nWeek: {week_key} ({week_start.strftime('%d %b %Y')} to {week_end.strftime('%d %b %Y')})")
        print(f"  Week start: {week_start}")
        print(f"  Week end: {week_end}")
        print(f"  Start date: {start_date}")
        print(f"  End date: {end_date}")
        
        # Check if this week falls within the specified date range
        if start_date and week_end < start_date:
            print(f"  Result: SKIP (week ends before start date)")
            continue
        if end_date and week_start > end_date:
            print(f"  Result: SKIP (week starts after end date)")
            continue
            
        print(f"  Result: INCLUDE (week is within date range)")

# Run the test
test_date_filtering()