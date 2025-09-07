import re
from datetime import datetime

def parse_timestamp(timestamp_str):
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

def analyze_group_events(messages):
    events = {
        'added': [],
        'left': [],
        'removed': [],
        'changed_subject': [],
        'changed_icon': [],
        'created': []
    }
    
    for msg in messages:
        text = msg['message'].lower()
        sender = msg['sender']
        timestamp = msg['timestamp']

        if 'added' in text:
            match = re.search(r'(.+?) added (.+)', msg['message'], re.IGNORECASE)
            if match:
                adder = match.group(1)
                added_person = match.group(2)
                events['added'].append({
                    'timestamp': timestamp,
                    'adder': adder,
                    'added_person': added_person,
                    'raw_message': msg['message']
                })
        
        elif 'left' in text:
            match = re.search(r'(.+?) left', msg['message'], re.IGNORECASE)
            if match:
                person_left = match.group(1)
                events['left'].append({
                    'timestamp': timestamp,
                    'person': person_left,
                    'raw_message': msg['message']
                })

        elif 'removed' in text:
            match = re.search(r'(.+?) removed (.+)', msg['message'], re.IGNORECASE)
            if match:
                remover = match.group(1)
                removed_person = match.group(2)
                events['removed'].append({
                    'timestamp': timestamp,
                    'remover': remover,
                    'removed_person': removed_person,
                    'raw_message': msg['message']
                })
        
        elif 'changed the subject to' in text:
            match = re.search(r'(.+?) changed the subject to "(.+)"', msg['message'], re.IGNORECASE)
            if match:
                changer = match.group(1)
                new_subject = match.group(2)
                events['changed_subject'].append({
                    'timestamp': timestamp,
                    'changer': changer,
                    'new_subject': new_subject,
                    'raw_message': msg['message']
                })

        elif 'changed this group\'s icon' in text:
            match = re.search(r'(.+?) changed this group\'s icon', msg['message'], re.IGNORECASE)
            if match:
                changer = match.group(1)
                events['changed_icon'].append({
                    'timestamp': timestamp,
                    'changer': changer,
                    'raw_message': msg['message']
                })

        elif 'created group' in text:
            match = re.search(r'(.+?) created group', msg['message'], re.IGNORECASE)
            if match:
                creator = match.group(1)
                events['created'].append({
                    'timestamp': timestamp,
                    'creator': creator,
                    'raw_message': msg['message']
                })
    
    return events

def get_event_counts(events):
    return {
        'added': len(events['added']),
        'left': len(events['left']),
        'removed': len(events['removed']),
        'changed_subject': len(events['changed_subject']),
        'changed_icon': len(events['changed_icon']),
        'created': len(events['created'])
    }

def get_event_details(events, event_type, start_date=None, end_date=None):
    event_list = events.get(event_type, [])
    if start_date or end_date:
        filtered_events = []
        for event in event_list:
            event_date = parse_timestamp(event['timestamp'])
            if event_date is None:
                continue
            if start_date and event_date < start_date:
                continue
            if end_date and event_date > end_date:
                continue
            filtered_events.append(event)
        return filtered_events
    
    return event_list

def get_top_removers(events, limit=5):
    remover_counts = {}
    for event in events['removed']:
        remover = event['remover']
        remover_counts[remover] = remover_counts.get(remover, 0) + 1
    
    sorted_removers = sorted(remover_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_removers[:limit]