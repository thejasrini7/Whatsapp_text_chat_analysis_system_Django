import re
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import os
from django.conf import settings
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY)

# Initialize the model with fallback
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    logger.warning(f"Could not initialize gemini-2.0-flash, falling back to gemini-flash-latest: {e}")
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
    except Exception as e2:
        logger.warning(f"Could not initialize gemini-flash-latest, falling back to gemini-pro-latest: {e2}")
        model = genai.GenerativeModel('gemini-pro-latest')

def generate_fallback_summary(messages):
    """Generate structured summary with actual message content when AI is unavailable"""
    if not messages:
        return "**ACTIVITY OVERVIEW**: No messages during this week\n**MAIN DISCUSSION TOPICS**: No conversations recorded"
    
    # Basic statistics
    total_messages = len(messages)
    users = set(msg['sender'] for msg in messages)
    user_count = len(users)
    
    # Most active user
    user_msg_count = {}
    for msg in messages:
        user = msg['sender']
        user_msg_count[user] = user_msg_count.get(user, 0) + 1
    
    most_active_user = max(user_msg_count.items(), key=lambda x: x[1]) if user_msg_count else None
    
    # Extract actual message content (not system messages)
    actual_messages = []
    file_names = []
    conversation_snippets = []
    
    for msg in messages:
        message_text = msg['message']
        message_lower = message_text.lower()
        
        # Skip system messages
        if any(term in message_lower for term in ['media omitted', 'security code changed', 'tap to learn more', 'this message was deleted', 'messages and calls are end-to-end encrypted']):
            continue
            
        # Look for file names and documents
        if any(ext in message_lower for ext in ['.pdf', '.doc', '.jpg', '.png', '.mp4', '.xlsx']):
            file_names.append(message_text.strip())
        
        # Collect meaningful conversation content
        if len(message_text.strip()) >= 10:  # Meaningful messages
            conversation_snippets.append(f"{msg['sender']}: {message_text.strip()[:100]}..." if len(message_text) > 100 else f"{msg['sender']}: {message_text.strip()}")
            actual_messages.append(message_text)
    
    # Build structured summary with actual content
    summary_parts = []
    
    # Activity Overview
    summary_parts.append(f"**ACTIVITY OVERVIEW**: {total_messages} messages from {user_count} participants during this week")
    
    # Key Participants
    if most_active_user:
        percentage = round((most_active_user[1] / total_messages) * 100)
        summary_parts.append(f"**KEY PARTICIPANTS**: {most_active_user[0]} was most active with {most_active_user[1]} messages ({percentage}% of activity)")
    
    # Main Discussion Topics with actual content
    if file_names or conversation_snippets:
        summary_parts.append("**MAIN DISCUSSION TOPICS**:")
        
        topic_count = 1
        # Add file/document sharing topics
        for file_name in file_names[:3]:  # Show up to 3 files
            summary_parts.append(f"- Topic {topic_count}: Document shared - \"{file_name}\"")
            topic_count += 1
        
        # Add conversation content from ALL participants, not just most active
        participant_messages = {}
        for snippet in conversation_snippets[:15]:  # Get more messages
            participant = snippet.split(':')[0]
            if participant not in participant_messages:
                participant_messages[participant] = []
            participant_messages[participant].append(snippet)
        
        # Distribute topics across different participants
        for participant, messages in list(participant_messages.items())[:7]:  # Up to 7 different participants
            if topic_count <= 7:
                sample_msg = messages[0] if messages else f"{participant}: [No detailed message]"
                summary_parts.append(f"- Topic {topic_count}: {sample_msg}")
                topic_count += 1
    else:
        # If no meaningful content found, show the actual raw messages to debug
        if len(messages) > 0:
            sample_messages = []
            for i, msg in enumerate(messages[:5]):  # Show first 5 messages for debugging
                sample_messages.append(f"{msg['sender']}: {msg['message'][:100]}")
            
            summary_parts.append("**MAIN DISCUSSION TOPICS**:")
            for i, sample in enumerate(sample_messages, 1):
                summary_parts.append(f"- Topic {i}: {sample}")
        else:
            summary_parts.append("**MAIN DISCUSSION TOPICS**: No messages found")
    
    # Social Dynamics with actual interaction content
    if user_count > 1 and conversation_snippets:
        summary_parts.append(f"**SOCIAL DYNAMICS**: Active interaction among {user_count} participants with meaningful exchanges")
        if len(conversation_snippets) >= 2:
            summary_parts.append(f"Sample interaction: {conversation_snippets[0]}")
    elif user_count > 1:
        summary_parts.append(f"**SOCIAL DYNAMICS**: Group interaction among {user_count} participants")
    else:
        summary_parts.append("**SOCIAL DYNAMICS**: Individual activity only")
    
    return '\n'.join(summary_parts)

def generate_with_gemini(prompt):
    """Generate content using Google Gemini AI SDK"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        # Check if it's a quota exceeded error
        if "429" in str(e) or "quota" in str(e).lower():
            return "QUOTA_EXCEEDED"
        return "API_ERROR"

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
        prompt = "Generate a brief summary in 3-4 bullet points. Focus only on the most important topics and key events. Keep it concise and easy to understand. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information.\n\n" + chat_text
        response = generate_with_gemini(prompt)
        
        # Check if API quota exceeded or error occurred
        if response == "QUOTA_EXCEEDED":
            return generate_fallback_summary(messages)
        elif response == "API_ERROR":
            return "Summary temporarily unavailable due to technical issues."
        else:
            return response
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def generate_user_messages(messages):
    """Generate enhanced user messages with meaningful content and timestamps"""
    if not messages:
        return []
    
    # Filler words to remove
    filler_words = {
        'ok', 'okay', 'okk', 'okkkk', 'hmm', 'hmmm', 'yes', 'yeah', 'yep', 'yup', 
        'no', 'nope', 'ha', 'haha', 'lol', 'lmao', 'hehe', 'hi', 'hello', 'hey', 
        'bye', 'byee', 'thanks', 'thank', 'welcome', 'sure', 'fine', 'good', 
        'nice', 'great', 'cool', 'awesome', 'alright', 'right', 'correct'
    }
    
    # System message patterns to exclude
    system_message_patterns = [
        'security code', 'tap to learn more', 'changed the subject', 'added', 'removed',
        'left the group', 'joined using', 'created group', 'media omitted', 
        'this message was deleted', 'changed this group', 'end-to-end encrypted'
    ]
    
    user_messages = []
    user_topics = {}  # Track topics per user
    
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if dt:
            formatted_datetime = dt.strftime('%d %b %Y, %I:%M %p')
        else:
            formatted_datetime = msg['timestamp']
        
        user = msg['sender']
        message_text = msg['message'].strip()
        
        # Skip system messages more comprehensively
        is_system_message = any(pattern in message_text.lower() for pattern in system_message_patterns)
        if is_system_message:
            continue
            
        # Clean message by removing filler words
        words = message_text.split()
        cleaned_words = []
        for word in words:
            # Remove punctuation for comparison but keep in display
            word_clean = word.lower().strip('.,!?;:')
            if word_clean not in filler_words and len(word_clean) > 1:
                cleaned_words.append(word)
        
        # Only include messages with substantial content
        if len(cleaned_words) >= 2 or len(message_text) >= 15:
            cleaned_message = ' '.join(cleaned_words) if cleaned_words else message_text
            
            # Format message content for better readability
            formatted_message = format_message_content(cleaned_message)
            
            # Extract topics for this user
            if user not in user_topics:
                user_topics[user] = set()
            
            # Simple topic extraction
            significant_words = [w.lower() for w in cleaned_words if len(w) > 4 and w.isalpha()]
            user_topics[user].update(significant_words[:3])  # Add first 3 significant words
            
            user_messages.append({
                'sender': user,
                'cleaned_message': formatted_message,
                'formatted_datetime': formatted_datetime,
                'original_message': message_text,
                'message_length': len(formatted_message)
            })
    
    # Add topics to each message (limit to 5 topics per user)
    for msg in user_messages:
        user = msg['sender']
        msg['topics'] = list(user_topics.get(user, set()))[:5]
    
    # Sort by timestamp (most recent first)
    user_messages.sort(key=lambda x: x['formatted_datetime'], reverse=True)
    
    return user_messages

def format_message_content(message):
    """Format message content for better readability with bullet points"""
    if not message:
        return message
    
    # Remove escape characters
    message = message.replace('\\n', '\n').replace('\\t', ' ').replace(r'\[', '[').replace(r'\]', ']')
    message = re.sub(r'\\(.)', r'\1', message)  # Remove backslashes before special characters
    
    # If message contains structured content, format it with bullet points
    if any(indicator in message for indicator in ['*', '**', '१)', '२)', 'विषय', 'दिनांक']):
        # Split by common delimiters and create bullet points
        lines = message.replace('*', '').split()
        formatted_lines = []
        current_line = []
        
        for word in lines:
            # Check for numbered points
            if word.startswith(('१)', '२)', '३)', '४)', '५)', '1)', '2)', '3)', '4)', '5)')):
                if current_line:
                    formatted_lines.append(' '.join(current_line))
                    current_line = []
                formatted_lines.append(f"• {word}")
            elif word in ['विषय:-', 'दिनांक-', 'वार-', 'टिप-']:
                if current_line:
                    formatted_lines.append(' '.join(current_line))
                    current_line = []
                formatted_lines.append(f"• {word}")
            else:
                current_line.append(word)
        
        if current_line:
            formatted_lines.append(' '.join(current_line))
        
        # Join with proper line breaks
        return ' '.join(formatted_lines) if len(formatted_lines) <= 3 else '\n'.join(formatted_lines[:5]) + '...'
    
    # For regular messages, just clean up extra spaces
    return ' '.join(message.split())

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
    """Clean and format structured summary text following memory specifications"""
    if not summary:
        return ""
    
    # If it's an error message or quota message, return it as-is
    if any(keyword in summary.lower() for keyword in ['error', 'unavailable', 'quota', 'limits']):
        return summary
    
    # Handle structured format with sections
    if "**ACTIVITY OVERVIEW**" in summary or "**MAIN DISCUSSION TOPICS**" in summary:
        # Clean up the structured format but preserve the sections
        lines = summary.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                # Skip system message references
                if any(term in line.lower() for term in ['media omitted', 'security code', 'tap to learn']):
                    continue
                # Remove escape characters and clean formatting
                line = line.replace('\\n', '\n').replace('\\t', ' ').replace(r'\[', '[').replace(r'\]', ']')
                line = re.sub(r'\\(.)', r'\1', line)  # Remove backslashes before special characters
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    # Handle bullet point format (fallback)
    lines = summary.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that mention system messages
        if any(term in line.lower() for term in ['media omitted', 'security code', 'tap to learn', 'changed security', 'message deleted']):
            continue
        
        # Remove escape characters and clean formatting
        line = line.replace('\\n', '\n').replace('\\t', ' ').replace(r'\[', '[').replace(r'\]', ']')
        line = re.sub(r'\\(.)', r'\1', line)  # Remove backslashes before special characters
        
        # Process bullet points
        if line.startswith(('•', '-', '*')) or (len(line) >= 2 and line[0].isdigit() and line[1] == '.'):
            # Remove bullet character and clean
            if line[0].isdigit() and line[1] == '.':
                line = line[2:].lstrip()
            else:
                line = line[1:].lstrip()
            
            line = re.sub(r'\s+', ' ', line).strip()
            
            if line and len(line) > 5:
                line = line[0].upper() + line[1:] if line else line
                cleaned_lines.append(f"* {line}")
        else:
            # For non-bullet lines, clean and format
            line = re.sub(r'\s+', ' ', line).strip()
            if line and len(line) > 5:
                cleaned_lines.append(f"* {line}")
    
    # If no meaningful content found
    if not cleaned_lines:
        return "**MAIN DISCUSSION TOPICS**: Mostly media sharing and brief exchanges during this week"
    
    return '\n'.join(cleaned_lines)

def generate_weekly_summary(messages, start_date_str=None, end_date_str=None):
    """Generate comprehensive weekly summaries with detailed discussion points for filtered date range"""
    if not messages:
        return []
    
    # Parse start and end dates if provided
    start_date = None
    end_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # Group messages by week (messages are already filtered by views.py)
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

    # Process all weeks that have messages within the filtered date range
    for week_key, week_messages in sorted(weeks.items()):
        # Only process weeks that have messages
        if not week_messages:
            continue
            
        # Check if this week falls within the specified date range
        week_start = datetime.strptime(week_key, '%Y-%m-%d')
        week_end = week_start + timedelta(days=6)
        
        # Skip weeks that are outside the specified date range
        if start_date and week_end < start_date:
            continue
        if end_date and week_start > end_date:
            continue
            
        # Basic statistics for this week
        total_messages = len(week_messages)
        users = set(msg['sender'] for msg in week_messages)
        user_count = len(users)
        
        # User activity analysis
        user_msg_count = {}
        for msg in week_messages:
            user = msg['sender']
            user_msg_count[user] = user_msg_count.get(user, 0) + 1
        
        # Sort users by activity
        sorted_users = sorted(user_msg_count.items(), key=lambda x: x[1], reverse=True)
        most_active_user = sorted_users[0] if sorted_users else None
        
        week_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in week_messages])

        try:
            # Enhanced prompt to extract EXACT conversation content and quotes
            exact_content_prompt = f"""Analyze this week's WhatsApp conversation and create a detailed summary showing EXACTLY what was discussed with actual quotes and specific content.

**CRITICAL INSTRUCTIONS**:
1. Show ACTUAL messages, file names, and specific content shared
2. Include exact quotes in original language (Hindi/Marathi/English)
3. Mention specific documents, files, or links shared by name
4. Show real conversation content from ALL participants, not just the most active user
5. Include messages from different people - distribute topics across various participants
6. For Social Dynamics, describe what ALL people said to each other
7. Include specific advice, instructions, or information shared by anyone
8. DO NOT focus only on the most active user - show diversity of participants
9. DO NOT generalize - show the actual conversation content from everyone

**REQUIRED STRUCTURE**:
**ACTIVITY OVERVIEW**: {total_messages} messages from {user_count} participants during this week

**KEY PARTICIPANTS**: [Most active member and their specific contributions]

**MAIN DISCUSSION TOPICS** (Show 5-7 actual conversation topics from ALL participants, not just the most active):
- Topic 1: [Any participant]: "[Actual quote from message]"
- Topic 2: [Different participant]: "[Exact message content in original language]"
- Topic 3: [Another participant]: "[Real conversation exchange]"
- [Continue with conversations from various participants]

**IMPORTANT EVENTS**: [Actual announcements, documents shared, or decisions made with exact content]

**COMMUNICATION PATTERNS**: [When specific conversations happened]

**ACTION ITEMS**: [Exact instructions or tasks mentioned in messages]

**SOCIAL DYNAMICS**: [What ALL participants said to each other - include quotes from different people]

Week's conversation content:
{week_text}"""
            
            response = generate_with_gemini(exact_content_prompt)
            
            # Check if API quota exceeded or error occurred
            if response == "QUOTA_EXCEEDED":
                summary = generate_fallback_summary(week_messages)
            elif response == "API_ERROR":
                summary = "Summary temporarily unavailable due to technical issues."
            else:
                summary = response
                # Clean the summary text
                summary = clean_summary_text(summary)

        except Exception as e:
            # Even if there's an error, we should still include this week in the results
            # Use fallback summary
            try:
                summary = generate_fallback_summary(week_messages)
            except Exception as fallback_error:
                summary = f"Error generating summary: {str(e)}. Fallback error: {str(fallback_error)}"
        
        monday = datetime.strptime(week_key, '%Y-%m-%d')
        sunday = monday + timedelta(days=6)
        date_range = f"{monday.strftime('%d %b %Y')} to {sunday.strftime('%d %b %Y')}" 
        
        weekly_summaries.append({
            'week_start': week_key,
            'date_range': date_range,
            'summary': summary,
            'message_count': len(week_messages),
            'participant_count': user_count,
            'most_active_user': most_active_user[0] if most_active_user else None
        })
    
    return weekly_summaries

def generate_brief_summary(messages):
    """Generate a comprehensive brief summary with detailed insights"""
    if not messages:
        return "No messages found in the selected date range."

    # Extract date range more accurately
    start_date = None
    end_date = None
    parsed_dates = []
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if dt:
            parsed_dates.append(dt)

    if parsed_dates:
        start_date = min(parsed_dates)
        end_date = max(parsed_dates)

    date_range_text = ""
    if start_date and end_date:
        date_range_text = f"Summary from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\n\n"

    # Basic statistics for enhanced insights
    total_messages = len(messages)
    users = set(msg['sender'] for msg in messages)
    user_count = len(users)

    # Most active user
    user_msg_count = {}
    for msg in messages:
        user = msg['sender']
        user_msg_count[user] = user_msg_count.get(user, 0) + 1

    most_active_user = max(user_msg_count.items(), key=lambda x: x[1]) if user_msg_count else None

    # Calculate activity patterns
    hourly_activity = {}
    daily_activity = {}
    for msg in messages:
        dt = parse_timestamp(msg['timestamp'])
        if dt:
            hour = dt.hour
            day = dt.strftime('%A')
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            daily_activity[day] = daily_activity.get(day, 0) + 1

    peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
    peak_day = max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else None

    chat_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in messages])

    try:
        # Enhanced prompt to ensure comprehensive topic coverage from ALL participants
        comprehensive_prompt = f"""Analyze this extensive chat conversation (covering {start_date.strftime('%Y-%m-%d') if start_date else 'unknown'} to {end_date.strftime('%Y-%m-%d') if end_date else 'unknown'}) and create a comprehensive summary that captures the FULL DIVERSITY of discussions.

**CRITICAL REQUIREMENTS**:
1. This is a LONG-TERM summary covering many months - show VARIETY of topics
2. Include discussions from MULTIPLE DIFFERENT participants, not just 1-2 people
3. Show DIVERSE conversation topics - academic, technical, social, administrative, etc.
4. Extract topics from DIFFERENT TIME PERIODS throughout the date range
5. Include conversations about DIFFERENT SUBJECTS and themes
6. Show the BREADTH of group activities and discussions
7. DO NOT focus only on one participant or one type of discussion
8. Capture ALL major themes and conversation threads

**REQUIRED SECTIONS**:
**OVERVIEW**: {total_messages} messages from {user_count} participants from {start_date.strftime('%Y-%m-%d') if start_date else 'unknown'} to {end_date.strftime('%Y-%m-%d') if end_date else 'unknown'}

**KEY PARTICIPANTS**: {most_active_user[0] if most_active_user else 'N/A'} was most active with {most_active_user[1] if most_active_user else 0} messages, but show contributions from multiple participants

**MAIN DISCUSSION TOPICS** (Show 7-10 DIVERSE topics from VARIOUS participants covering DIFFERENT themes):
- Topic 1: [Academic discussions] - [Quote from Student A]
- Topic 2: [Technical/Programming content] - [Quote from Student B]
- Topic 3: [Project coordination] - [Quote from Student C]
- Topic 4: [Social activities/events] - [Quote from different participant]
- Topic 5: [Administrative announcements] - [Quote from another participant]
- Topic 6: [Resource sharing] - [Quote from yet another participant]
- Topic 7: [Group collaboration] - [Quote from different student]
- [Continue with varied topics from different people and time periods]

**ACTIVITY PATTERNS**: Peak activity at {peak_hour if peak_hour is not None else 'N/A'}:00 on {peak_day if peak_day else 'N/A'} - describe various types of discussions during different periods

**COMMUNICATION STYLE**: Describe how {user_count} participants interacted across multiple themes and subjects

**NOTABLE CONVERSATIONS**: Highlight significant discussions from different participants and time periods

Conversation content spanning {total_messages} messages:
{chat_text[:8000]}..."""

        response = generate_with_gemini(comprehensive_prompt)

        # Check if API quota exceeded or error occurred
        if response == "QUOTA_EXCEEDED":
            # Enhanced fallback summary with actual content for brief summary
            fallback_parts = []

            # Overview with actual conversation analysis
            fallback_parts.append(f"**OVERVIEW**: {total_messages} messages from {user_count} participants from {start_date.strftime('%Y-%m-%d') if start_date else 'unknown'} to {end_date.strftime('%Y-%m-%d') if end_date else 'unknown'}")

            # Most active user with their contributions
            if most_active_user:
                fallback_parts.append(f"**KEY PARTICIPANTS**: {most_active_user[0]} was most active with {most_active_user[1]} messages")

            # Extract actual message content for topics
            actual_messages = []
            file_names = []
            meaningful_conversations = []
            
            for msg in messages:
                message_text = msg['message']
                message_lower = message_text.lower()
                
                # Skip only specific system messages
                if any(term in message_lower for term in ['<media omitted>', 'security code changed', 'this message was deleted']):
                    continue
                    
                # Look for documents and files
                if any(ext in message_lower for ext in ['.pdf', '.doc', '.jpg', '.png', '.mp4', '.xlsx', '.jpeg', '.docx']):
                    file_names.append(f"{msg['sender']}: {message_text.strip()}")
                
                # Collect meaningful conversations
                if len(message_text.strip()) >= 15:  # Substantial messages
                    meaningful_conversations.append(f"{msg['sender']}: {message_text.strip()[:120]}..." if len(message_text) > 120 else f"{msg['sender']}: {message_text.strip()}")
                    actual_messages.append(message_text)

            # Main topics with comprehensive coverage from all participants
            fallback_parts.append("**MAIN DISCUSSION TOPICS**:")
            topic_count = 1
            
            # Ensure diverse topic coverage by sampling from different participants
            unique_participants = set()
            topic_categories = {
                'documents': [],
                'technical': [],
                'academic': [],
                'social': [],
                'general': []
            }
            
            # Categorize conversations for diversity
            for conversation in meaningful_conversations:
                participant = conversation.split(':')[0]
                content = conversation.lower()
                
                if any(ext in content for ext in ['.pdf', '.doc', '.jpg', '.png', '.mp4', '.xlsx']):
                    topic_categories['documents'].append(conversation)
                elif any(term in content for term in ['code', 'programming', 'function', 'algorithm', 'hackerrank']):
                    topic_categories['technical'].append(conversation)
                elif any(term in content for term in ['assignment', 'exam', 'study', 'project', 'homework']):
                    topic_categories['academic'].append(conversation)
                elif any(term in content for term in ['birthday', 'celebration', 'meeting', 'event']):
                    topic_categories['social'].append(conversation)
                else:
                    topic_categories['general'].append(conversation)
            
            # Add diverse topics from each category
            for category, conversations in topic_categories.items():
                for conv in conversations[:2]:  # Max 2 from each category
                    if topic_count <= 10:  # Increase to 10 topics for comprehensive coverage
                        participant = conv.split(':')[0]
                        if participant not in unique_participants or len(unique_participants) < 7:
                            fallback_parts.append(f"- Topic {topic_count}: {conv}")
                            unique_participants.add(participant)
                            topic_count += 1
            
            # Add remaining diverse conversations if needed
            for conversation in meaningful_conversations:
                if topic_count <= 10:
                    participant = conversation.split(':')[0]
                    if participant not in unique_participants:
                        fallback_parts.append(f"- Topic {topic_count}: {conversation}")
                        unique_participants.add(participant)
                        topic_count += 1
            
            if not file_names and not meaningful_conversations:
                # Show sample messages for debugging
                for i, msg in enumerate(messages[:5], 1):
                    fallback_parts.append(f"- Topic {i}: {msg['sender']}: {msg['message'][:80]}...")

            # Activity patterns
            if peak_hour is not None:
                hour_12 = peak_hour % 12 or 12
                am_pm = "AM" if peak_hour < 12 else "PM"
                fallback_parts.append(f"**ACTIVITY PATTERNS**: Peak activity at {hour_12}:00 {am_pm}")

            if peak_day:
                fallback_parts.append(f"**ACTIVITY PATTERNS**: Most active day was {peak_day}")

            # Communication style with actual insights
            if len(meaningful_conversations) > 0:
                fallback_parts.append(f"**COMMUNICATION STYLE**: Active discussions with {len(meaningful_conversations)} substantial exchanges")
            else:
                fallback_parts.append("**COMMUNICATION STYLE**: Mostly brief exchanges and media sharing")

            return f"{date_range_text}" + '\n'.join(fallback_parts)

        elif response == "API_ERROR":
            return "Summary temporarily unavailable due to technical issues."
        else:
            summary = response
            # Clean the summary text
            summary = clean_summary_text(summary)
            return f"{date_range_text}{summary}"

    except Exception as e:
        return f"Error generating summary: {str(e)}"

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
            prompt = "Generate a very brief daily summary in 1-2 bullet points. Focus only on key topics or events discussed that day. Each bullet point must start with '*' and be concise. Use **bold** for important terms, *italic* for emphasis, and <span style='color:red'>red text</span> for critical information.\n\n" + day_text
            response = generate_with_gemini(prompt)
            
            # Check if API quota exceeded or error occurred
            if response == "QUOTA_EXCEEDED":
                summary = generate_fallback_summary(day_messages)
            elif response == "API_ERROR":
                summary = "Summary temporarily unavailable due to technical issues."
            else:
                summary = response
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