import os
import re
import json
import csv
import os
import requests
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from dotenv import load_dotenv
from .models import ChatFile
from .config import GEMINI_API_KEY, MAX_CHARS_FOR_ANALYSIS
from .utils import parse_timestamp, filter_messages_by_date
from .business_metrics import calculate_business_metrics
from .group_event import (
    analyze_group_events,
    get_event_counts,
    get_event_details,
    get_top_removers,
    _normalize_events,
    _filter_normalized,
    compute_timeseries,
    compute_distribution,
    compute_most_active_day,
    compute_top_contributors,
    extract_unique_actors,
)
from .sentiment_analyzer import analyze_sentiment
from .summary_generator import (
    generate_total_summary, 
    generate_user_messages, 
    get_users_in_messages,
    generate_user_messages_for_user,
    generate_weekly_summary,
    generate_brief_summary,
    generate_daily_user_messages,
    generate_user_wise_detailed_report
)

load_dotenv()

# Use Google Gemini API
MODEL_NAME = "gemini-1.5-pro"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}/generateContent"

def generate_fallback_answer(question, messages):
    """Generate a comprehensive fallback answer when AI is unavailable"""
    if not messages:
        return "I don't have any messages to analyze for this date range."
    
    question_lower = question.lower()
    
    # Analyze basic statistics
    total_messages = len(messages)
    users = set(msg['sender'] for msg in messages)
    user_count = len(users)
    
    # User activity analysis
    user_msg_count = {}
    for msg in messages:
        user = msg['sender']
        user_msg_count[user] = user_msg_count.get(user, 0) + 1
    
    most_active_user = max(user_msg_count.items(), key=lambda x: x[1]) if user_msg_count else None
    
    # Extract meaningful content and filter system messages
    meaningful_messages = []
    meeting_messages = []
    file_messages = []
    topic_messages = []
    
    for msg in messages:
        message_text = msg['message'].strip()
        message_lower = message_text.lower()
        
        # Skip system messages
        if any(term in message_lower for term in ['security code', 'media omitted', 'tap to learn', 'left', 'added', 'removed']):
            continue
            
        # Collect meaningful messages
        if len(message_text) > 15:
            meaningful_messages.append(msg)
            
            # Look for meeting-related content
            if any(word in message_lower for word in ['meet', 'meeting', 'मिटिंग', 'मीटिंग', 'दौरा', 'आयोजन', 'उपस्थित']):
                meeting_messages.append(msg)
                
            # Look for file/document sharing
            if any(ext in message_lower for ext in ['.pdf', '.doc', '.jpg', '.png', '.mp4', '.xlsx', '.jpeg', '.docx']):
                file_messages.append(msg)
                
            # Collect other substantial content
            if len(message_text) > 30:
                topic_messages.append(msg)
    
    # Handle different types of questions
    if any(word in question_lower for word in ['meet', 'meeting', 'मिटिंग', 'दौरा']):
        if meeting_messages:
            answer = "📅 **Meetings Found:**\n\n"
            for i, msg in enumerate(meeting_messages[:5], 1):  # Show up to 5 meetings
                # Extract date/time from message content
                meeting_content = msg['message'][:200] + "..." if len(msg['message']) > 200 else msg['message']
                answer += f"**{i}. Meeting on {msg['timestamp']}**\n"
                answer += f"👤 Organized by: {msg['sender']}\n"
                answer += f"📝 Details: {meeting_content}\n\n"
            return answer
        else:
            return "No meetings found in the conversation history for the selected date range."
    
    elif any(word in question_lower for word in ['most active', 'who', 'active user']):
        if most_active_user:
            # Show top 3 users
            sorted_users = sorted(user_msg_count.items(), key=lambda x: x[1], reverse=True)
            answer = "👥 **Most Active Users:**\n\n"
            for i, (user, count) in enumerate(sorted_users[:3], 1):
                percentage = round((count/total_messages)*100, 1)
                answer += f"**{i}. {user}**: {count} messages ({percentage}%)\n"
            return answer
        else:
            return "Unable to determine user activity from the available data."
    
    elif any(word in question_lower for word in ['how many', 'total', 'messages', 'count']):
        answer = f"📊 **Message Statistics:**\n\n"
        answer += f"• **Total Messages**: {total_messages}\n"
        answer += f"• **Total Users**: {user_count}\n"
        answer += f"• **Date Range**: {messages[0]['timestamp']} to {messages[-1]['timestamp']}\n"
        answer += f"• **Average per User**: {round(total_messages/user_count, 1)} messages\n"
        return answer
    
    elif any(word in question_lower for word in ['file', 'document', 'pdf', 'shared']):
        if file_messages:
            answer = "📎 **Files/Documents Shared:**\n\n"
            for i, msg in enumerate(file_messages[:5], 1):
                answer += f"**{i}. {msg['timestamp']}**\n"
                answer += f"👤 Shared by: {msg['sender']}\n"
                answer += f"📄 File: {msg['message'][:100]}...\n\n"
            return answer
        else:
            return "No files or documents were shared in the selected time period."
    
    elif any(word in question_lower for word in ['when', 'time', 'day', 'date']):
        if messages:
            # Analyze message patterns by time/day
            from collections import defaultdict
            day_counts = defaultdict(int)
            hour_counts = defaultdict(int)
            
            for msg in messages:
                try:
                    # Extract day and hour information
                    timestamp = msg['timestamp']
                    # Simple parsing - could be enhanced
                    if ',' in timestamp:
                        date_part = timestamp.split(',')[0]
                        day_counts[date_part] += 1
                except:
                    continue
            
            if day_counts:
                most_active_day = max(day_counts.items(), key=lambda x: x[1])
                answer = f"📅 **Activity Timeline:**\n\n"
                answer += f"• **Most Active Day**: {most_active_day[0]} ({most_active_day[1]} messages)\n"
                answer += f"• **Total Date Range**: {messages[0]['timestamp']} to {messages[-1]['timestamp']}\n"
                answer += f"• **Total Days with Activity**: {len(day_counts)}\n"
                return answer
        
        return f"Messages range from {messages[0]['timestamp']} to {messages[-1]['timestamp']}."
    
    elif any(word in question_lower for word in ['topic', 'discuss', 'about', 'content', 'summary']):
        if topic_messages:
            answer = "💬 **Main Discussion Topics:**\n\n"
            # Group messages by sender to show diverse content
            user_topics = {}
            for msg in topic_messages[:15]:
                user = msg['sender']
                if user not in user_topics:
                    user_topics[user] = []
                if len(user_topics[user]) < 2:  # Max 2 topics per user
                    content = msg['message'][:120] + "..." if len(msg['message']) > 120 else msg['message']
                    user_topics[user].append({
                        'content': content,
                        'timestamp': msg['timestamp']
                    })
            
            topic_count = 1
            for user, topics in list(user_topics.items())[:5]:  # Show up to 5 users
                for topic in topics:
                    answer += f"**{topic_count}. {topic['timestamp']}**\n"
                    answer += f"👤 {user}: {topic['content']}\n\n"
                    topic_count += 1
                    if topic_count > 10:  # Max 10 topics total
                        break
                if topic_count > 10:
                    break
                    
            return answer
        else:
            return "The conversation appears to contain mostly brief exchanges or media sharing."
    
    elif any(word in question_lower for word in ['list', 'show', 'all']):
        # General listing based on context
        if 'meet' in question_lower or 'मिटिंग' in question_lower:
            # Already handled above
            return generate_fallback_answer("meetings", messages)
        elif 'user' in question_lower:
            answer = "👥 **All Users:**\n\n"
            sorted_users = sorted(user_msg_count.items(), key=lambda x: x[1], reverse=True)
            for i, (user, count) in enumerate(sorted_users, 1):
                percentage = round((count/total_messages)*100, 1)
                answer += f"{i}. **{user}**: {count} messages ({percentage}%)\n"
            return answer
        else:
            # Show general overview
            answer = "📋 **Chat Overview:**\n\n"
            answer += f"• **{total_messages} messages** from **{user_count} users**\n"
            answer += f"• **Time Period**: {messages[0]['timestamp']} to {messages[-1]['timestamp']}\n"
            if meeting_messages:
                answer += f"• **{len(meeting_messages)} meetings** mentioned\n"
            if file_messages:
                answer += f"• **{len(file_messages)} files** shared\n"
            answer += f"• **Most Active**: {most_active_user[0]} ({most_active_user[1]} messages)\n" if most_active_user else ""
            return answer
    
    else:
        # Enhanced general answer with actual insights
        answer = "📊 **Chat Analysis:**\n\n"
        answer += f"• **Total Activity**: {total_messages} messages from {user_count} users\n"
        if most_active_user:
            answer += f"• **Most Active**: {most_active_user[0]} with {most_active_user[1]} messages\n"
        if meeting_messages:
            answer += f"• **Meetings Mentioned**: {len(meeting_messages)} meeting-related discussions\n"
        if file_messages:
            answer += f"• **Files Shared**: {len(file_messages)} documents/media shared\n"
        answer += f"• **Time Range**: {messages[0]['timestamp']} to {messages[-1]['timestamp']}\n\n"
        answer += "💡 **Try asking**: 'List meetings', 'Who is most active?', 'What topics were discussed?', 'Show files shared'"
        return answer

def generate_with_gemini(prompt):
    """Generate content using Google Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params={"key": api_key}, json=data)
        response.raise_for_status()

        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']

    except requests.exceptions.RequestException as e:
        raise Exception(f"Gemini API error: {str(e)}")
    except KeyError as e:
        raise Exception(f"Unexpected response format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error calling Gemini API: {str(e)}")

def parse_whatsapp(file_path):
    messages = []
    current_message = None
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2}\u202F[AP]M) - (.*?): (.*)',
        r'(\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [AP]M) - (.*?): (.*)',
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?::\d{2})?(?: [AP]M)?)\] (.*?): (.*)',
        r'(\d{4}-\d{1,2}-\d{1,2}, \d{1,2}:\d{2}) - (.*?): (.*)',
        r'(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}) - (.*?): (.*)',
        r'(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2} [AP]M) - (.*?): (.*)'
    ]
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue    
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if current_message:
                        messages.append(current_message)
                    
                    timestamp, sender, message = match.groups()
                    current_message = {
                        'timestamp': timestamp,
                        'sender': sender,
                        'message': message
                    }
                    matched = True
                    break
            if not matched and current_message:
                if current_message['message']:
                    current_message['message'] += '\n' + line
                else:
                    current_message['message'] = line
    if current_message:
        messages.append(current_message)
    return messages

def get_group_name_from_file(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace('_', ' ').replace('-', ' ')
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def load_all_chats():
    chat_data = {}
    chat_files = ChatFile.objects.all()
    print(f"Found {len(chat_files)} chat files in database")
    for chat_file in chat_files:
        file_path = chat_file.file.path
        group_name = chat_file.group_name
        print(f"Loading file: {chat_file.original_filename}, group: {group_name}, path: {file_path}")
        try:
            messages = parse_whatsapp(file_path)
            print(f"Parsed {len(messages)} messages from {chat_file.original_filename}")
            if group_name not in chat_data:
                chat_data[group_name] = {
                    'filenames': [chat_file.original_filename],
                    'file_ids': [chat_file.id],
                    'messages': messages
                }
            else:
                chat_data[group_name]['filenames'].append(chat_file.original_filename)
                chat_data[group_name]['file_ids'].append(chat_file.id)
                chat_data[group_name]['messages'].extend(messages)
        except Exception as e:
            print(f"Error loading {chat_file.original_filename}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Loaded groups: {list(chat_data.keys())}")
    # Sort messages by timestamp for each group
    for group_name, data in chat_data.items():
        messages = data['messages']
        messages.sort(key=lambda msg: parse_timestamp(msg['timestamp']) or datetime.min)

    return chat_data

def index(request):
    # Redirect legacy root to the new Home page to surface the modern UI
    return redirect('home')

# New pages for modern UI

def home(request):
    # Home page with upload + group selection
    return render(request, 'chatapp/home.html')

def dashboard(request):
    # Render the old dashboard with date hints
    group = request.GET.get('group', '')
    context = {'group': group}
    if group:
        chat_data = load_all_chats()
        if group in chat_data:
            messages = chat_data[group]['messages']
            if messages:
                from .utils import parse_timestamp
                dates = [parse_timestamp(msg['timestamp']) for msg in messages if parse_timestamp(msg['timestamp'])]
                if dates:
                    first_date = min(dates)
                    last_date = max(dates)
                    context['first_date'] = first_date.strftime('%d / %m / %Y')
                    context['last_date'] = last_date.strftime('%d / %m / %Y')
    return render(request, 'chatapp/dashboard.html', context)

def react_dashboard(request):
    # React + Tailwind + Recharts powered dashboard
    group = request.GET.get('group', '')
    context = {
        'group': group
    }
    if group:
        chat_data = load_all_chats()
        if group in chat_data:
            messages = chat_data[group]['messages']
            if messages:
                from .utils import parse_timestamp
                dates = [parse_timestamp(msg['timestamp']) for msg in messages if parse_timestamp(msg['timestamp'])]
                if dates:
                    start_date = min(dates).strftime('%d / %m / %Y')
                    end_date = max(dates).strftime('%d / %m / %Y')
                    context['chat_start_date'] = start_date
                    context['chat_end_date'] = end_date
    return render(request, 'chatapp/react_dashboard.html', context)

# ------------------- Group Events Dashboard (Bootstrap) -------------------

def group_events_page(request):
    return render(request, 'chatapp/group_events_dashboard.html')

@require_http_methods(["GET"])
def get_group_dates(request):
    group = request.GET.get('group', '')
    if not group:
        return JsonResponse({"error": "No group specified"}, status=400)
    chat_data = load_all_chats()
    if group not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    messages = chat_data[group]['messages']
    if not messages:
        return JsonResponse({"error": "No messages"}, status=400)
    from .utils import parse_timestamp
    dates = [parse_timestamp(msg['timestamp']) for msg in messages if parse_timestamp(msg['timestamp'])]
    if not dates:
        return JsonResponse({"error": "No valid dates"}, status=400)
    start_date = min(dates).strftime('%d / %m / %Y')
    end_date = max(dates).strftime('%d / %m / %Y')
    return JsonResponse({"start_date": start_date, "end_date": end_date})

@csrf_exempt
@require_http_methods(["POST"])
def group_events_analytics(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    event_types = data.get('event_types')  # list or None
    user = data.get('user')  # string or None

    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)

    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)

    messages = chat_data[group_name]['messages']
    # First pass filter coarse by date for performance
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)

    # Build events and normalize
    events = analyze_group_events(filtered_messages)
    normalized = _normalize_events(events)

    # Prepare datetime bounds for fine filtering
    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    rows = _filter_normalized(normalized, start_dt, end_dt, event_types, user)

    # Aggregations
    timeseries = compute_timeseries(rows)
    distribution = compute_distribution(rows)
    most_active = compute_most_active_day(timeseries)
    top_contributors = compute_top_contributors(rows, limit=5)

    # Card counts from filtered rows
    card_counts = {'added': 0, 'left': 0, 'removed': 0, 'changed_subject': 0, 'changed_icon': 0, 'created': 0}
    for r in rows:
        card_counts[r['event_type']] += 1

    actors = extract_unique_actors(rows)

    return JsonResponse({
        "event_counts": card_counts,
        "insights": {
            "most_active_day": most_active,  # e.g., {date, total, ...}
            "total_events": distribution.get('total', 0),
            "top_contributors": top_contributors,
        },
        "timeseries": timeseries,
        "distribution": distribution,
        "actors": actors,
    })

@csrf_exempt
@require_http_methods(["POST"])
def group_events_logs(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    event_types = data.get('event_types')
    user = data.get('user')

    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)

    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)

    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    if not filtered_messages:
        return JsonResponse({"events": []})

    events = analyze_group_events(filtered_messages)
    normalized = _normalize_events(events)

    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    rows = _filter_normalized(normalized, start_dt, end_dt, event_types, user)

    # Shape rows for table
    table_rows = []
    for r in rows:
        table_rows.append({
            'event_type': r['event_type'],
            'actor': r['actor'],
            'target': r['target'],
            'timestamp': r['dt'].strftime('%d-%b-%Y %I:%M %p'),
            'details': r['details'] or '',
        })

    return JsonResponse({"events": table_rows})

@require_http_methods(["GET"])
def get_groups(request):
    chat_data = load_all_chats()
    groups = list(chat_data.keys())
    return JsonResponse({"groups": groups})

@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        if not file_obj:
            return JsonResponse({"error": "No file provided"}, status=400)
        if not file_obj.name.endswith('.txt'):
            return JsonResponse({"error": "Only .txt files are supported"}, status=400)
        group_name = get_group_name_from_file(file_obj.name)
        chat_file = ChatFile(
            file=file_obj,
            original_filename=file_obj.name,
            group_name=group_name
        )
        chat_file.save()
        return JsonResponse({
            "success": True,
            "group_name": group_name,
            "file_id": chat_file.id
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
@require_http_methods(["POST"])
def delete_file(request):
    data = json.loads(request.body)
    file_id = data.get('file_id')
    if not file_id:
        return JsonResponse({"error": "No file ID provided"}, status=400)
    try:
        chat_file = ChatFile.objects.get(id=file_id)
        if chat_file.file:
            chat_file.file.delete()
        chat_file.delete()
        return JsonResponse({"success": True})
    except ChatFile.DoesNotExist:
        return JsonResponse({"error": "File not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_uploaded_files(request):
    files = []
    chat_files = ChatFile.objects.all().order_by('-uploaded_at')
    for chat_file in chat_files:
        files.append({
            "id": chat_file.id,
            "original_filename": chat_file.original_filename,
            "group_name": chat_file.group_name,
            "uploaded_at": chat_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse({"files": files})

@csrf_exempt
@require_http_methods(["POST"])
def summarize(request):
    data = json.loads(request.body)
    group_name = data.get('group_name')
    summary_type = data.get('summary_type', 'total')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    user = data.get('user')
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    if summary_type == 'total':
        summary = generate_total_summary(filtered_messages)
        return JsonResponse({"summary_type": "total", "summary": summary})
    
    elif summary_type == 'user_messages':
        user_messages = generate_user_messages(filtered_messages)
        return JsonResponse({"summary_type": "user_messages", "user_messages": user_messages})
    
    elif summary_type == 'user_wise':
        users = get_users_in_messages(filtered_messages)
        return JsonResponse({"summary_type": "user_wise", "users": users})
    
    elif summary_type == 'user_messages_for_user':
        if not user:
            return JsonResponse({"error": "No user specified"}, status=400)
        user_messages = generate_user_messages_for_user(filtered_messages, user)
        return JsonResponse({"summary_type": "user_messages_for_user", "user": user, "user_messages": user_messages})
    
    elif summary_type == 'weekly_summary':
        weekly_summaries = generate_weekly_summary(filtered_messages, start_date_str, end_date_str)
        return JsonResponse({"summary_type": "weekly_summary", "weekly_summaries": weekly_summaries})
    
    elif summary_type == 'brief':
        summary = generate_brief_summary(filtered_messages)
        return JsonResponse({"summary_type": "brief", "summary": summary})
    
    elif summary_type == 'daily_user_messages':
        daily_summaries = generate_daily_user_messages(filtered_messages)
        return JsonResponse({"summary_type": "daily_user_messages", "daily_summaries": daily_summaries})
    
    elif summary_type == 'user_wise_detailed':
        if not user:
            return JsonResponse({"error": "No user specified"}, status=400)
        user_messages = generate_user_wise_detailed_report(filtered_messages, user)
        return JsonResponse({"summary_type": "user_wise_detailed", "user": user, "user_messages": user_messages})
    
    else:
        return JsonResponse({"error": "Invalid summary type"}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def ask_question(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    user_question = data.get('question')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    if not user_question:
        return JsonResponse({"error": "No question provided"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    chat_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in filtered_messages])
    
    if len(chat_text) > MAX_CHARS_FOR_ANALYSIS:
        chat_text = chat_text[-MAX_CHARS_FOR_ANALYSIS:]
    
    try:
        # Enhanced prompt for better AI responses
        prompt = f"""You are a WhatsApp chat analyzer. Analyze the following chat data and answer the user's question with specific, detailed information.

IMPORTANT INSTRUCTIONS:
- Provide SPECIFIC answers with dates, times, names, and actual content
- For meeting questions: List actual meetings with dates, organizers, and details
- For "who" questions: Provide names and statistics
- For "what" questions: Describe actual topics discussed with examples
- For "when" questions: Give specific dates and times
- Use emojis and formatting for better readability
- Extract exact information from the chat content

Chat Data:
{chat_text}

User Question: {user_question}

Provide a comprehensive answer with specific details from the chat:"""
        
        response = generate_with_gemini(prompt)
        
        # Handle potential API issues
        if response == "QUOTA_EXCEEDED":
            # Generate fallback answer based on the question and chat content
            answer = generate_fallback_answer(user_question, filtered_messages)
        elif response == "API_ERROR":
            answer = "I'm experiencing technical difficulties with the AI service. Please try again in a few moments."
        else:
            answer = response
            
        return JsonResponse({"answer": answer})
    except Exception as e:
        # Generate fallback answer for any errors
        try:
            answer = generate_fallback_answer(user_question, filtered_messages)
            return JsonResponse({"answer": answer})
        except Exception as fallback_error:
            return JsonResponse({"error": f"Unable to process your question at this time. Please try again later."}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def group_events(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    print(f"Found {len(filtered_messages)} messages in date range")
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    events = analyze_group_events(filtered_messages)
    event_counts = get_event_counts(events)
    top_removers = get_top_removers(events)
    
    print(f"Event counts: {event_counts}")
    print(f"Total events found: {len(events)}")
    
    return JsonResponse({
        "event_counts": event_counts,
        "top_removers": top_removers
    })

@csrf_exempt
@require_http_methods(["POST"])
def event_details(request):
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    event_type = data.get('event_type')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    if not event_type:
        return JsonResponse({"error": "No event type provided"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    events = analyze_group_events(filtered_messages)
    event_details = get_event_details(events, event_type)
    
    return JsonResponse({
        "event_type": event_type,
        "events": event_details
    })

def analyze_group_events(messages):
    """Analyze group events from messages"""
    events = []
    
    print(f"Analyzing {len(messages)} messages for group events...")
    
    for i, message in enumerate(messages):
        text = message.get('message', '').lower()
        timestamp = message.get('timestamp', '')
        sender = message.get('sender', 'Unknown')
        original_message = message.get('message', '')
        
        # Debug: Print first 10 messages to see what we're working with
        if i < 10:
            print(f"Message {i}: '{original_message}' (sender: {sender})")
        
        # Check for different event types with better pattern matching
        if is_added_event(text, original_message):
            print(f"Found ADDED event: '{original_message}'")
            added_details = extract_added_details(original_message)
            events.append({
                'type': 'added',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': added_details,
                'added_person': extract_person_name(original_message, 'added'),
                'adder': sender
            })
        elif is_left_event(text, original_message):
            print(f"Found LEFT event: '{original_message}'")
            left_details = extract_left_details(original_message)
            events.append({
                'type': 'left',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': left_details,
                'person': extract_person_name(original_message, 'left')
            })
        elif is_removed_event(text, original_message):
            print(f"Found REMOVED event: '{original_message}'")
            removed_details = extract_removed_details(original_message)
            events.append({
                'type': 'removed',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': removed_details,
                'removed_person': extract_person_name(original_message, 'removed'),
                'remover': sender
            })
        elif is_subject_changed_event(text, original_message):
            print(f"Found SUBJECT CHANGED event: '{original_message}'")
            subject_details = extract_subject_change_details(original_message)
            events.append({
                'type': 'changed_subject',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': subject_details,
                'changer': sender,
                'new_subject': extract_subject_name(original_message)
            })
        elif is_icon_changed_event(text, original_message):
            print(f"Found ICON CHANGED event: '{original_message}'")
            events.append({
                'type': 'changed_icon',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': 'Group icon was changed',
                'changer': sender
            })
        elif is_group_created_event(text, original_message):
            print(f"Found GROUP CREATED event: '{original_message}'")
            events.append({
                'type': 'created',
                'timestamp': timestamp,
                'sender': sender,
                'raw_message': original_message,
                'details': 'Group was created',
                'creator': sender
            })
    
    print(f"Found {len(events)} total events")
    return events

def is_added_event(text, original_message):
    """Check if message is an 'added' event"""
    patterns = [
        'added',
        'joined',
        'was added',
        'has been added',
        'added to the group',
        'joined the group',
        'was added to the group'
    ]
    return any(pattern in text for pattern in patterns)

def is_left_event(text, original_message):
    """Check if message is a 'left' event"""
    patterns = [
        'left',
        'exited',
        'left the group',
        'exited the group',
        'has left',
        'has exited'
    ]
    return any(pattern in text for pattern in patterns)

def is_removed_event(text, original_message):
    """Check if message is a 'removed' event"""
    patterns = [
        'removed',
        'kicked',
        'was removed',
        'has been removed',
        'removed from the group',
        'kicked from the group',
        'was kicked'
    ]
    return any(pattern in text for pattern in patterns)

def is_subject_changed_event(text, original_message):
    """Check if message is a 'subject changed' event"""
    patterns = [
        'changed the subject',
        'changed subject',
        'subject changed',
        'changed group subject',
        'group subject changed'
    ]
    return any(pattern in text for pattern in patterns)

def is_icon_changed_event(text, original_message):
    """Check if message is an 'icon changed' event"""
    patterns = [
        'changed the group icon',
        'changed group icon',
        'group icon changed',
        'changed the icon',
        'icon changed'
    ]
    return any(pattern in text for pattern in patterns)

def is_group_created_event(text, original_message):
    """Check if message is a 'group created' event"""
    patterns = [
        'created group',
        'group created',
        'created the group',
        'group was created'
    ]
    return any(pattern in text for pattern in patterns)

def get_event_details(events, event_type):
    """Get details for specific event type"""
    filtered_events = [event for event in events if event['type'] == event_type]
    
    # Sort by timestamp (newest first)
    filtered_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return filtered_events

def extract_added_details(message):
    """Extract details from 'added' event message"""
    import re
    
    # Try to extract who added whom
    patterns = [
        r'(\w+(?:\s+\w+)*)\s+added\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+has\s+added\s+(\w+(?:\s+\w+)*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            adder = match.group(1).strip()
            added_person = match.group(2).strip()
            return f"{adder} added {added_person}"
    
    # Fallback
    if 'added' in message.lower():
        parts = message.split('added')
        if len(parts) > 1:
            return f"Added: {parts[1].strip()}"
    return "Member was added to the group"

def extract_left_details(message):
    """Extract details from 'left' event message"""
    import re
    
    # Try to extract who left
    patterns = [
        r'(\w+(?:\s+\w+)*)\s+left',
        r'(\w+(?:\s+\w+)*)\s+exited',
        r'(\w+(?:\s+\w+)*)\s+has\s+left',
        r'(\w+(?:\s+\w+)*)\s+has\s+exited'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            person = match.group(1).strip()
            return f"{person} left the group"
    
    # Fallback
    if 'left' in message.lower():
        return f"Left: {message.replace('left', '').strip()}"
    elif 'exited' in message.lower():
        return f"Exited: {message.replace('exited', '').strip()}"
    return "Member left the group"

def extract_removed_details(message):
    """Extract details from 'removed' event message"""
    import re
    
    # Try to extract who removed whom
    patterns = [
        r'(\w+(?:\s+\w+)*)\s+removed\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+kicked\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+has\s+removed\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+has\s+kicked\s+(\w+(?:\s+\w+)*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            remover = match.group(1).strip()
            removed_person = match.group(2).strip()
            return f"{remover} removed {removed_person}"
    
    # Fallback
    if 'removed' in message.lower():
        parts = message.split('removed')
        if len(parts) > 1:
            return f"Removed: {parts[1].strip()}"
    elif 'kicked' in message.lower():
        parts = message.split('kicked')
        if len(parts) > 1:
            return f"Kicked: {parts[1].strip()}"
    return "Member was removed from the group"

def extract_subject_change_details(message):
    """Extract details from subject change event message"""
    # Common patterns: "User changed the subject to 'New Subject'"
    if 'changed the subject' in message:
        if 'to' in message:
            parts = message.split('to')
            if len(parts) > 1:
                return f"Subject changed to: {parts[1].strip()}"
        return "Group subject was changed"
    return "Group subject was changed"

def extract_person_name(message, event_type):
    """Extract person name from event message"""
    import re
    
    if event_type == 'added':
        # Patterns: "John Doe added Jane Smith", "John Doe added Jane Smith and 2 others"
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+added\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+has\s+added\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+added\s+(\w+(?:\s+\w+)*)\s+to\s+the\s+group'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(2).strip()
        
        # Fallback: split by 'added'
        if 'added' in message.lower():
            parts = message.split('added')
            if len(parts) > 1:
                name = parts[1].strip()
                # Remove common suffixes
                name = re.sub(r'\s+and\s+\d+\s+others?', '', name)
                name = re.sub(r'\s+to\s+the\s+group', '', name)
                return name.strip()
                
    elif event_type == 'left':
        # Patterns: "John Doe left", "John Doe exited"
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+left',
            r'(\w+(?:\s+\w+)*)\s+exited',
            r'(\w+(?:\s+\w+)*)\s+has\s+left',
            r'(\w+(?:\s+\w+)*)\s+has\s+exited'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback
        if 'left' in message.lower():
            return message.replace('left', '').strip()
        elif 'exited' in message.lower():
            return message.replace('exited', '').strip()
            
    elif event_type == 'removed':
        # Patterns: "John Doe removed Jane Smith", "John Doe kicked Jane Smith"
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+removed\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+kicked\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+has\s+removed\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+has\s+kicked\s+(\w+(?:\s+\w+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(2).strip()
        
        # Fallback
        if 'removed' in message.lower():
            parts = message.split('removed')
            if len(parts) > 1:
                return parts[1].strip()
        elif 'kicked' in message.lower():
            parts = message.split('kicked')
            if len(parts) > 1:
                return parts[1].strip()
    
    return 'Unknown'

def extract_subject_name(message):
    """Extract new subject name from subject change message"""
    if 'changed the subject to' in message:
        parts = message.split('to')
        if len(parts) > 1:
            subject = parts[1].strip()
            # Remove quotes if present
            subject = subject.strip('"').strip("'")
            return subject
    return 'New Subject'

def get_event_counts(events):
    """Get count of each event type"""
    counts = {
        'added': 0,
        'left': 0,
        'removed': 0,
        'changed_subject': 0,
        'changed_icon': 0,
        'created': 0
    }
    
    for event in events:
        event_type = event.get('type', '')
        if event_type in counts:
            counts[event_type] += 1
    
    return counts

def get_top_removers(events):
    """Get top users who removed others"""
    remover_counts = {}
    
    for event in events:
        if event.get('type') == 'removed':
            remover = event.get('remover', 'Unknown')
            if remover in remover_counts:
                remover_counts[remover] += 1
            else:
                remover_counts[remover] = 1
    
    # Sort by count and return top 5
    sorted_removers = sorted(remover_counts.items(), key=lambda x: x[1], reverse=True)
    return [{'user': user, 'count': count} for user, count in sorted_removers[:5]]

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
@require_http_methods(["POST"])
def sentiment(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    print(f"Sentiment analysis request: group={group_name}, start={start_date_str}, end={end_date_str}")
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    try:
        chat_data = load_all_chats()
        print(f"Available groups: {list(chat_data.keys())}")
        
        if group_name not in chat_data:
            return JsonResponse({"error": "Group not found"}, status=404)
        
        messages = chat_data[group_name]['messages']
        print(f"Total messages in group: {len(messages)}")
        
        # Filter messages by date range
        filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
        print(f"Filtered messages count: {len(filtered_messages)}")
        
        if not filtered_messages:
            return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
        
        # Perform sentiment analysis
        print(f"About to call analyze_sentiment with {len(filtered_messages)} messages")
        result = analyze_sentiment(filtered_messages)
        print(f"Sentiment analysis completed. Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            print(f"Sentiment breakdown: {result.get('sentiment_breakdown')}")
            print(f"Overall sentiment: {result.get('overall_sentiment')}")
        else:
            print(f"Unexpected result type: {result}")
        
        # Ensure we have the expected format for frontend
        if 'sentiment_breakdown' not in result:
            result['sentiment_breakdown'] = result.get('overall_sentiment', {'positive': 0, 'neutral': 0, 'negative': 0})
        
        # Add total count for frontend display
        total_count = sum(result['sentiment_breakdown'].values())
        result['total_analyzed'] = total_count
        
        return JsonResponse(result)
        
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def activity_analysis(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    specific_date_str = data.get('specific_date')  # For hourly analysis
    week_start_str = data.get('week_start')       # For weekly analysis
    week_end_str = data.get('week_end')           # For weekly analysis
    start_date_str = data.get('start_date')       # Generic range
    end_date_str = data.get('end_date')
    user_filter = data.get('user')                # Optional user filter
    include_messages = bool(data.get('include_messages', False))
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    try:
        chat_data = load_all_chats()
        if group_name not in chat_data:
            return JsonResponse({"error": "Group not found"}, status=404)
    except Exception as e:
        print(f"Error loading chat data: {e}")
        return JsonResponse({"error": "Failed to load chat data"}, status=500)
    
    messages = chat_data[group_name]['messages']
    
    # Pre-filter by user if provided
    if user_filter:
        messages = [m for m in messages if m.get('sender') == user_filter]
    
    # Filter messages based on the provided date parameters
    if specific_date_str:
        # For hourly analysis on a specific date
        start_date = datetime.strptime(specific_date_str, '%Y-%m-%d')
        end_date = start_date.replace(hour=23, minute=59, second=59)
        filtered_messages = [msg for msg in messages if 
                            parse_timestamp(msg['timestamp']) and 
                            start_date <= parse_timestamp(msg['timestamp']) <= end_date]
        analysis_type = "hourly"
    elif week_start_str and week_end_str:
        # For weekly analysis
        start_date = datetime.strptime(week_start_str, '%Y-%m-%d')
        end_date = datetime.strptime(week_end_str, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        filtered_messages = [msg for msg in messages if 
                            parse_timestamp(msg['timestamp']) and 
                            start_date <= parse_timestamp(msg['timestamp']) <= end_date]
        analysis_type = "weekly"
    elif start_date_str and end_date_str:
        # Generic date range analysis
        filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
        analysis_type = "range"
    else:
        # Default to all messages
        filtered_messages = messages
        analysis_type = "all"
    

    # Apply user filter again after date filtering (safety)
    if user_filter:
        filtered_messages = [m for m in filtered_messages if m.get('sender') == user_filter]

    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)

    try:
        # For very large datasets, limit the number of messages to prevent timeout
        max_messages = 50000  # Limit to 50k messages for performance
        if len(filtered_messages) > max_messages:
            print(f"Large dataset detected ({len(filtered_messages)} messages), limiting to {max_messages}")
            filtered_messages = filtered_messages[:max_messages]
        
        raw_metrics = calculate_business_metrics(filtered_messages)
    except Exception as e:
        print(f"Error calculating business metrics: {e}")
        return JsonResponse({"error": "Failed to calculate metrics"}, status=500)

    # Transform to frontend-expected shape
    # Hourly: array 0..23 aligned with labels
    hourly_activity = [int(raw_metrics.get('activity_by_hour', {}).get(h, 0)) for h in range(24)]

    # Daily: array 0..6 (Sun..Sat) aligned with labels
    day_index = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6}
    daily_activity = [0 for _ in range(7)]
    for day_name, cnt in raw_metrics.get('activity_by_day', {}).items():
        idx = day_index.get(day_name)
        if idx is not None:
            daily_activity[idx] = int(cnt)

    message_counts = raw_metrics.get('messages_per_user', {})

    # Build list of all users for the selected period ignoring the user filter
    available_users = []
    try:
        base_msgs = chat_data[group_name]['messages']
        if specific_date_str:
            _start = datetime.strptime(specific_date_str, '%Y-%m-%d')
            _end = _start.replace(hour=23, minute=59, second=59)
            period_msgs = [m for m in base_msgs if parse_timestamp(m['timestamp']) and _start <= parse_timestamp(m['timestamp']) <= _end]
        elif week_start_str and week_end_str:
            _start = datetime.strptime(week_start_str, '%Y-%m-%d')
            _end = datetime.strptime(week_end_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            period_msgs = [m for m in base_msgs if parse_timestamp(m['timestamp']) and _start <= parse_timestamp(m['timestamp']) <= _end]
        elif start_date_str and end_date_str:
            period_msgs = filter_messages_by_date(base_msgs, start_date_str, end_date_str)
        else:
            period_msgs = base_msgs
        available_users = sorted({m.get('sender') for m in period_msgs if m.get('sender')})
    except Exception:
        available_users = []

    # --- Week splitting logic for frontend week cards ---
    weeks = []
    if start_date_str and end_date_str:
        try:
            # Split the selected period into weeks (Monday-Sunday)
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Align start to previous Monday
            start_of_week = start_dt - timedelta(days=start_dt.weekday())
            current = start_of_week
            while current <= end_dt:
                week_start = current
                week_end = min(current + timedelta(days=6), end_dt)
                week_msgs = [m for m in filtered_messages if parse_timestamp(m['timestamp']) and week_start <= parse_timestamp(m['timestamp']) <= week_end]
                week_users = sorted({m.get('sender') for m in week_msgs if m.get('sender')})
                week_message_counts = {}
                for m in week_msgs:
                    sender = m.get('sender')
                    if sender:
                        week_message_counts[sender] = week_message_counts.get(sender, 0) + 1
                # Find most active user and peak hour for the week
                most_active_user = max(week_message_counts.items(), key=lambda x: x[1])[0] if week_message_counts else None
                # Hourly activity for the week
                week_hourly = {h: 0 for h in range(24)}
                for m in week_msgs:
                    dt = parse_timestamp(m['timestamp'])
                    if dt:
                        week_hourly[dt.hour] += 1
                peak_hour = max(week_hourly.items(), key=lambda x: x[1])[0] if week_hourly else None
                # Daily activity for the week (0=Sunday, 1=Monday, ..., 6=Saturday)
                week_daily = {i: 0 for i in range(7)}
                for m in week_msgs:
                    dt = parse_timestamp(m['timestamp'])
                    if dt:
                        # Convert weekday() to frontend format: 0=Sunday, 1=Monday, etc.
                        day_index = (dt.weekday() + 1) % 7  # Monday=0 -> Sunday=0, Tuesday=1 -> Monday=1, etc.
                        week_daily[day_index] += 1
                week_data = {
                    'start': week_start.strftime('%Y-%m-%d'),
                    'end': week_end.strftime('%Y-%m-%d'),
                    'message_count': len(week_msgs),
                    'users': week_users,
                    'message_counts': week_message_counts,
                    'most_active_user': most_active_user,
                    'peak_hour': peak_hour,
                    'daily_activity': {int(k): v for k, v in week_daily.items()},  # Convert string keys to int
                    'hourly_activity': {int(k): v for k, v in week_hourly.items()},  # Convert string keys to int
                    'messages': week_msgs,
                }
                print(f"Week {len(weeks)+1}: {week_data['start']} - {week_data['end']}, Messages: {len(week_msgs)}, Daily: {week_daily}, Hourly: {week_hourly}")
                weeks.append(week_data)
                current += timedelta(days=7)
        except Exception as e:
            print(f"Error in week splitting logic: {e}")
            # Continue without weeks data rather than failing completely

    activity_data = {
        'total_messages': raw_metrics.get('total_messages', 0),
        'total_users': raw_metrics.get('total_users', 0),
        'hourly_activity': hourly_activity,
        'daily_activity': daily_activity,
        'message_counts': message_counts,
        'analysis_type': analysis_type,
        'all_users': available_users,
        'weeks': weeks if weeks else None,
    }

    if include_messages:
        activity_data['messages'] = filtered_messages

    return JsonResponse(activity_data)

@csrf_exempt
@require_http_methods(["POST"])
def export_data(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    # For PDF export compatibility, define these as None if not present
    week_start_str = data.get('week_start', None)
    week_end_str = data.get('week_end', None)
    specific_date_str = data.get('specific_date', None)
    export_features = data.get('features', [])
    export_format = data.get('format', 'json')
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    export_data = {}
    
    if 'summary' in export_features or 'all' in export_features:
        export_data['summary'] = generate_total_summary(filtered_messages)
    
    if 'sentiment' in export_features or 'all' in export_features:
        export_data['sentiment'] = analyze_sentiment(filtered_messages)
    
    if 'activity' in export_features or 'all' in export_features:
        export_data['activity'] = calculate_business_metrics(filtered_messages)
    
    if 'events' in export_features or 'all' in export_features:
        events = analyze_group_events(filtered_messages)
        export_data['events'] = {
            'event_counts': get_event_counts(events),
            'top_removers': get_top_removers(events)
        }
    
    if 'messages' in export_features or 'all' in export_features:
        export_data['messages'] = filtered_messages
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{group_name}_chat_analysis_{timestamp}"
    
    if export_format == 'json':
        response = HttpResponse(json.dumps(export_data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        return response
    
    elif export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Sender', 'Message'])
        for msg in filtered_messages:
            writer.writerow([msg['timestamp'], msg['sender'], msg['message']])
        return response

    elif export_format == 'excel':
        try:
            import io
            import xlsxwriter
        except Exception as e:
            return JsonResponse({"error": "Excel export requires xlsxwriter"}, status=500)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet('Messages')
        headers = ['Timestamp', 'Sender', 'Message']
        for c, h in enumerate(headers):
            ws.write(0, c, h)
        for r, msg in enumerate(filtered_messages, start=1):
            ws.write(r, 0, msg.get('timestamp', ''))
            ws.write(r, 1, msg.get('sender', ''))
            ws.write(r, 2, msg.get('message', ''))
        workbook.close()
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response

    elif export_format == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            import io
        except Exception:
            return JsonResponse({"error": "PDF export requires reportlab"}, status=500)
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 2*cm
        p.setFont("Helvetica-Bold", 14)
        p.drawString(2*cm, y, f"Chat Analysis Report: {group_name}")
        y -= 1*cm
        p.setFont("Helvetica", 10)
        p.drawString(2*cm, y, f"Date range: {start_date_str or week_start_str or specific_date_str} - {end_date_str or week_end_str or specific_date_str}")
        y -= 1*cm
        p.setFont("Helvetica-Bold", 12)
        p.drawString(2*cm, y, "Messages:")
        y -= 0.7*cm
        p.setFont("Helvetica", 9)
        for msg in filtered_messages[:1000]:
            line = f"{msg.get('timestamp','')} - {msg.get('sender','')}: {msg.get('message','')[:150]}"
            if y < 2*cm:
                p.showPage(); y = height - 2*cm; p.setFont("Helvetica", 9)
            p.drawString(2*cm, y, line)
            y -= 0.5*cm
        p.showPage()
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        return response
    
    else:
        return JsonResponse({"error": "Unsupported export format"}, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def debug_groups(request):
    """Debug endpoint to list available groups and basic info"""
    try:
        chat_data = load_all_chats()
        groups_info = {}
        
        for group_name, group_data in chat_data.items():
            messages = group_data.get('messages', [])
            groups_info[group_name] = {
                'total_messages': len(messages),
                'first_message_date': None,
                'last_message_date': None
            }
            
            # Find date range
            dates = [parse_timestamp(msg['timestamp']) for msg in messages if parse_timestamp(msg['timestamp'])]
            if dates:
                groups_info[group_name]['first_message_date'] = min(dates).strftime('%Y-%m-%d')
                groups_info[group_name]['last_message_date'] = max(dates).strftime('%Y-%m-%d')
        
        return JsonResponse({
            'available_groups': list(chat_data.keys()),
            'groups_info': groups_info,
            'total_groups': len(chat_data)
        })
        
    except Exception as e:
        print(f"Error in debug_groups: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)


def health_check(request):
    """Health check endpoint for Render deployment"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'whatsapp-analytics'
    })