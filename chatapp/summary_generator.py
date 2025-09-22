import re
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

# Use lazy initialization for Groq client to prevent blocking at import time
MODEL_NAME = "deepseek-r1-distill-llama-70b"

def get_groq_client():
    """Initialize Groq client only when needed to prevent blocking at import time"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    return Groq(api_key=api_key, timeout=30.0)

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
        client = get_groq_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Generate a brief summary in 3-4 bullet points. Focus only on the most important topics and key events. Keep it concise and easy to understand. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information."},
                {"role": "user", "content": chat_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_user_messages(messages):
    if not messages:
        return "No messages found in the selected date range."
    
    formatted_messages = {}
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if dt:
            time_str = dt.strftime('%d %b %Y, %I:%M %p')
        else:
            time_str = msg['timestamp']
        
        user = msg['sender']
        if user not in formatted_messages:
            formatted_messages[user] = []
        
        formatted_messages[user].append({
            'timestamp': time_str,
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

def clean_summary_text(summary):
    """Clean and format summary text according to user requirements"""
    if not summary:
        return ""
    
    # Remove any introductory text before bullet points
    lines = summary.split('\n')
    cleaned_lines = []
    in_bullet_points = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a bullet point
        if line.startswith(('•', '-', '*')) or (len(line) >= 2 and line[0].isdigit() and line[1] == '.'):
            in_bullet_points = True
            # Remove bullet character and any extra spaces
            if line[0].isdigit() and line[1] == '.':
                line = line[2:].lstrip()
            else:
                line = line[1:].lstrip()
        
        # Only process lines that are part of bullet points
        if in_bullet_points:
            # Remove filler words
            line = re.sub(r'\bokayy\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\balright\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\bokay\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\blike\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\bneed to\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\bthat\b', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\band\b', '', line, flags=re.IGNORECASE)
            
            # Remove extra spaces between words but preserve formatting
            line = re.sub(r'(?<!\*|_|<|>)\s+(?!\*|_|<|>)', ' ', line)
            
            # Clean up any double spaces that might remain
            line = re.sub(r'\s+', ' ', line).strip()
            
            if line:
                # Capitalize first letter
                line = line[0].upper() + line[1:] if line else line
                cleaned_lines.append(f"* {line}")
    
    return '\n'.join(cleaned_lines)

def generate_weekly_summary(messages):
    """Generate a concise weekly summary of the conversation"""
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
            client = get_groq_client()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Generate a concise weekly summary in exactly 2-3 bullet points. Focus only on the most important topics, decisions, and events. Each bullet point must start with '*' and contain only the key information without any explanations, introductory text, or meta-commentary. Do not include any text before the first bullet point or after the last bullet point. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information."},
                    {"role": "user", "content": week_text}
                ]
            )
            summary = response.choices[0].message.content
            
            # Clean the summary text
            summary = clean_summary_text(summary)
            
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

def generate_brief_summary(messages):
    """Generate a very brief summary with key highlights only"""
    if not messages:
        return "No messages found in the selected date range."
    
    # Extract date range
    start_date = None
    end_date = None
    if messages:
        first_msg = messages[0]
        last_msg = messages[-1]
        start_date = parse_timestamp(first_msg['timestamp'])
        end_date = parse_timestamp(last_msg['timestamp'])
    
    date_range_text = ""
    if start_date and end_date:
        date_range_text = f"Summary from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\n\n"
    
    chat_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in messages])
    
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": f"Generate a very brief summary in 3-5 bullet points. Include key dates for important events. Focus only on the most critical information. Use direct language without explanations or meta-commentary. Avoid using first-person pronouns. Format as bullet points starting with *. Use this format:\n{date_range_text}* [Date]: [Key point 1]\n* [Date]: [Key point 2]\n* [Date]: [Key point 3]. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information."},
                {"role": "user", "content": chat_text}
            ]
        )
        summary = response.choices[0].message.content
        
        # Clean the summary text
        summary = clean_summary_text(summary)
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
    
    return summary

def generate_daily_user_messages(messages):
    """Generate day-by-day user messages with short summaries"""
    if not messages:
        return []
    
    # Group messages by date
    daily_messages = {}
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if not dt:
            continue
        date_key = dt.strftime('%Y-%m-%d')
        if date_key not in daily_messages:
            daily_messages[date_key] = []
        daily_messages[date_key].append(msg)
    
    daily_summaries = []
    for date_key, day_messages in sorted(daily_messages.items()):
        # Create short summary for the day
        day_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in day_messages])
        
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Generate a very brief daily summary in 1-2 bullet points. Focus only on key topics or events discussed that day. Each bullet point must start with '*' and be concise. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information."},
                    {"role": "user", "content": day_text}
                ]
            )
            summary = response.choices[0].message.content
            summary = clean_summary_text(summary)
        except Exception as e:
            summary = f"Error generating summary: {str(e)}"
        
        # Format date nicely
        date_obj = datetime.strptime(date_key, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d %b %Y')
        
        daily_summaries.append({
            'date': date_key,
            'formatted_date': formatted_date,
            'summary': summary,
            'message_count': len(day_messages),
            'messages': day_messages
        })
    
    return daily_summaries

def generate_user_wise_detailed_report(messages, user):
    """Generate detailed user-wise report with date and time for each message"""
    if not messages or not user:
        return []
    
    user_messages = []
    for msg in messages:
        if msg['sender'] == user:
            dt = parse_timestamp(msg['timestamp'])
            if dt:
                formatted_datetime = dt.strftime('%d %b %Y, %I:%M %p')
                date_only = dt.strftime('%d %b %Y')
                time_only = dt.strftime('%I:%M %p')
            else:
                formatted_datetime = msg['timestamp']
                date_only = msg['timestamp'].split(',')[0] if ',' in msg['timestamp'] else msg['timestamp']
                time_only = msg['timestamp'].split(',')[1].strip() if ',' in msg['timestamp'] else ""
            
            user_messages.append({
                'datetime': formatted_datetime,
                'date': date_only,
                'time': time_only,
                'message': msg['message']
            })
    
    return user_messages