import re
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "deepseek-r1-distill-llama-70b"

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

def generate_total_summary(messages):
    if not messages:
        return "No messages found in the selected date range."
    
    chat_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in messages])
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Summarize this WhatsApp conversation concisely:"},
                {"role": "user", "content": chat_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_user_messages(messages):
    if not messages:
        return "No messages found in the selected date range."
    
    formatted_messages = []
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if dt:
            time_str = dt.strftime('%d %b %Y, %I:%M %p')
        else:
            time_str = msg['timestamp']
        formatted_messages.append({
            'timestamp': time_str,
            'sender': msg['sender'],
            'message': msg['message']
        })
    
    return formatted_messages

def get_users_in_messages(messages):
    if not messages:
        return []
    users = set()
    for msg in messages:
        users.add(msg['sender'])
    
    return sorted(list(users))

def generate_user_messages_for_user(messages, user):
    if not messages:
        return []
    user_messages = []
    for msg in messages:
        if msg['sender'] == user:
            dt = parse_timestamp(msg['timestamp'])
            if dt:
                time_str = dt.strftime('%d %b %Y, %I:%M %p')
            else:
                time_str = msg['timestamp']
            
            user_messages.append({
                'timestamp': time_str,
                'message': msg['message']
            })
    
    return user_messages

def generate_weekly_summary(messages):
    """Generate a weekly summary of the conversation"""
    if not messages:
        return []

    weeks = {}
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
        monday = dt - timedelta(days=dt.weekday())
        week_key = monday.strftime('%Y-%m-%d')
        if week_key not in weeks:
            weeks[week_key] = []
        weeks[week_key].append(msg)

    weekly_summaries = []
    
    for week_key, week_messages in sorted(weeks.items()):
        week_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in week_messages])
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Summarize this WhatsApp conversation for the week. List the main topics discussed:"},
                    {"role": "user", "content": week_text}
                ]
            )
            summary = response.choices[0].message.content
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"

        monday = datetime.strptime(week_key, '%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        date_range = f"{monday.strftime('%d %b %Y')} to {sunday.strftime('%d %b %Y')}" 
        weekly_summaries.append({
            'week_start': week_key,
            'date_range': date_range,
            'summary': summary,
            'message_count': len(week_messages)
        })
    
    return weekly_summaries