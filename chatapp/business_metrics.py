from datetime import datetime
from collections import Counter, defaultdict
import re
from .utils import parse_timestamp

def calculate_business_metrics(messages):
    if not messages:
        return {"error": "No messages found"}
    
    metrics = {
        'total_messages': len(messages),
        'total_users': len(set(msg['sender'] for msg in messages)),
        'messages_per_user': {},
        'activity_by_hour': {},
        'activity_by_day': {},
        'activity_by_hour_with_users': {},
        'top_keywords': {},
        'business_keywords_count': {}
    }
    
    user_counts = Counter(msg['sender'] for msg in messages)
    metrics['messages_per_user'] = dict(user_counts)
    
    # Initialize activity_by_hour_with_users
    for hour in range(24):
        metrics['activity_by_hour_with_users'][hour] = {}
    
    for msg in messages:
        timestamp = parse_timestamp(msg['timestamp'])
        if timestamp:
            hour = timestamp.hour
            if hour not in metrics['activity_by_hour']:
                metrics['activity_by_hour'][hour] = 0
            metrics['activity_by_hour'][hour] += 1
            
            # Track user activity by hour
            sender = msg['sender']
            if sender not in metrics['activity_by_hour_with_users'][hour]:
                metrics['activity_by_hour_with_users'][hour][sender] = 0
            metrics['activity_by_hour_with_users'][hour][sender] += 1
    
    for msg in messages:
        timestamp = parse_timestamp(msg['timestamp'])
        if timestamp:
            day = timestamp.strftime('%A')
            if day not in metrics['activity_by_day']:
                metrics['activity_by_day'][day] = 0
            metrics['activity_by_day'][day] += 1
    
    all_text = ' '.join([msg['message'].lower() for msg in messages])
    words = re.findall(r'\b\w+\b', all_text)
    word_counts = Counter(words)
    
    common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an', 'the']
    
    filtered_words = {word: count for word, count in word_counts.items() if word not in common_words and len(word) > 2}
    metrics['top_keywords'] = dict(Counter(filtered_words).most_common(20))
    
    business_keywords = ['price', 'cost', 'order', 'delivery', 'payment', 'product', 'service', 'meeting', 'client', 'customer', 'project', 'deadline', 'invoice', 'contract', 'deal', 'offer', 'discount', 'profit', 'loss', 'revenue', 'sales', 'marketing', 'promotion']
    
    for keyword in business_keywords:
        count = all_text.count(keyword)
        if count > 0:
            metrics['business_keywords_count'][keyword] = count
    
    return metrics