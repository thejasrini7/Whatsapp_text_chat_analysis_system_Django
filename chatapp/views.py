import os
import re
import json
import csv
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import default_storage
from dotenv import load_dotenv
from .models import ChatFile
from .config import GROQ_API_KEY, MAX_CHARS_FOR_ANALYSIS
from .utils import parse_timestamp, filter_messages_by_date
from .business_metrics import calculate_business_metrics
from .group_event import analyze_group_events, get_event_counts, get_event_details, get_top_removers
from .sentiment_analyzer import analyze_sentiment
from .summary_generator import (
    generate_total_summary, 
    generate_user_messages, 
    get_users_in_messages,
    generate_user_messages_for_user,
    generate_weekly_summary
)
from .topic_analyzer import extract_topics
from groq import Groq

load_dotenv()
client = Groq(api_key=GROQ_API_KEY)

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
    for chat_file in chat_files:
        file_path = chat_file.file.path
        group_name = chat_file.group_name 
        try:
            messages = parse_whatsapp(file_path)
            chat_data[group_name] = {
                'filename': chat_file.original_filename,
                'file_id': chat_file.id,
                'messages': messages
            }
        except Exception as e:
            print(f"Error loading {chat_file.original_filename}: {e}")
    return chat_data

def index(request):
    return render(request, 'chatapp/index.html')

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
        weekly_summaries = generate_weekly_summary(filtered_messages)
        return JsonResponse({"summary_type": "weekly_summary", "weekly_summaries": weekly_summaries})
    
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
        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on WhatsApp chat history. Be concise and specific."},
                {"role": "user", "content": f"Answer this question based on the following WhatsApp chat:\n\n{chat_text}\n\nQuestion: {user_question}"}
            ]
        )
        answer = response.choices[0].message.content
        return JsonResponse({"answer": answer})
    except Exception as e:
        return JsonResponse({"error": f"Error generating answer: {str(e)}"}, status=500)

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
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    events = analyze_group_events(filtered_messages)
    event_counts = get_event_counts(events)
    top_removers = get_top_removers(events)
    
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
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    result = analyze_sentiment(filtered_messages)
    return JsonResponse(result)

@csrf_exempt
@require_http_methods(["POST"])
def topic_analysis(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    group_name = data.get('group_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    top_n = int(data.get('top_n', 5))
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    filtered_messages = filter_messages_by_date(messages, start_date_str, end_date_str)
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    topics = extract_topics(filtered_messages, top_n=top_n)
    return JsonResponse({"topics": topics})

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
    
    if not group_name:
        return JsonResponse({"error": "Invalid group name"}, status=400)
    
    chat_data = load_all_chats()
    if group_name not in chat_data:
        return JsonResponse({"error": "Group not found"}, status=404)
    
    messages = chat_data[group_name]['messages']
    
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
    else:
        # Default to all messages
        filtered_messages = messages
        analysis_type = "all"
    
    if not filtered_messages:
        return JsonResponse({"error": "No messages found in the selected date range"}, status=400)
    
    activity_data = calculate_business_metrics(filtered_messages)
    activity_data['analysis_type'] = analysis_type
    
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
    
    if 'topics' in export_features or 'all' in export_features:
        export_data['topics'] = extract_topics(filtered_messages, top_n=10)
    
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
    
    else:
        return JsonResponse({"error": "Unsupported export format"}, status=400)