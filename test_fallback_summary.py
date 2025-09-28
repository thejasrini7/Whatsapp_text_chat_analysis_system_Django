from datetime import datetime

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

# Test with sample messages
sample_messages = [
    {
        'sender': 'John Doe',
        'message': 'Hello everyone! How is the project going?',
        'timestamp': '03/06/24, 10:30 AM'
    },
    {
        'sender': 'Jane Smith',
        'message': 'I just finished the first part of the analysis. Here are my findings.',
        'timestamp': '03/06/24, 11:15 AM'
    },
    {
        'sender': 'Bob Johnson',
        'message': 'Great work Jane! I have some questions about the methodology.',
        'timestamp': '03/06/24, 11:45 AM'
    },
    {
        'sender': 'Alice Williams',
        'message': 'I uploaded the project_report.pdf to the shared folder.',
        'timestamp': '03/06/24, 12:30 PM'
    }
]

print("Testing fallback summary generation:")
print("=" * 50)
result = generate_fallback_summary(sample_messages)
print(result)