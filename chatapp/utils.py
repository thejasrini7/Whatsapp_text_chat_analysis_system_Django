from datetime import datetime

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object"""
    timestamp_str = timestamp_str.replace('\u202F', ' ')
    formats = [
        '%m/%d/%y, %I:%M %p',
        '%m/%d/%Y, %I:%M %p',
        '%m/%d/%y, %H:%M',
        '%m/%d/%Y, %H:%M',
        '%Y-%m-%d, %H:%M',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            pass
    return None

def filter_messages_by_date(messages, start_date_str, end_date_str):
    """Filter messages by date range"""
    if not start_date_str and not end_date_str:
        return messages
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
    filtered_messages = []
    for msg in messages:
        msg_date = parse_timestamp(msg['timestamp'])
        if msg_date is None:
            continue
        if start_date and msg_date < start_date:
            continue
        if end_date and msg_date > end_date:
            continue
        filtered_messages.append(msg)
    return filtered_messages