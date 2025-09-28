import re

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

# Test the function with the example text
test_text = r"""*KEY PARTICIPANTS*: Sf Arra Abhi Medhane was the most active participant with 11 messages, followed by Sf Mangesh Baskar Sir with 5 messages. Sf Kalpanjay Nathe contributed 9 messages containing multimedia content related to field data. Jagannath Dagudu Bpadke shared an image file, and a user with phone number +91 94045 32865 sent a thank you message. A user with phone number +91 79725 22099 shared an audio file.

*MAIN DISCUSSION TOPICS*:

*   *Topic 1: Field Data and Observations: Sf Kalpanjay Nathe and Sf Arra Abhi Medhane shared numerous media files and observations related to grape cultivation, focusing on aspects such as recut plots, cane development, rootstock, and irrigation. - "Field day \n\nRecut plot Arra Red Selection 5 & 6\n\nFarmer name-Sachin Balasaheb Kushare\n\nDays after recut- 70\n\nNo. Of canes ready- 18-22" - *Sf Kalpanjay Nathe

*   *Topic 2: Grape Cultivation Study Tour Announcement: Sf Arra Abhi Medhane announced an organized field study tour for ARRA Red Selection 5 and 6, focusing on recut plots and various management practices. - "*\n\nनमस्कार, 🍇 आरा रेड सिलेक्शन ५,६ अभ्यास दौरा आयोजन 🍇 *विषय:- रिकट प्लॉट १)पाणी,अन्नद्रव्य,रोग व किड व्यवस्थापन २)कॅनोपी व्यवस्थापन ३)राहिलेले गॅप कव्हर करणे" - Sf Arra Abhi Medhane

*   *Topic 3: Field Study Tour Logistics: Sf Arra Abhi Medhane provided the location for the study tour and emphasized the importance of bringing a notebook and pen for notes. - "location: https://maps.google.com/?q=20.1720672,73.8586819 प्लॉट चे लोकेशन 👆" - *Sf Arra Abhi Medhane

*   *Topic 5: Fertilizer Schedule Sharing: Sf Mangesh Baskar Sir shared a PDF document outlining the fertilizer schedule for ARRA Red Sele-5 Ownroot for 2024. - *"ARRA Red Sele-5 Ownroot खत वेळापत्रक 2024.pdf" - Sf Mangesh Baskar Sir

*   *Topic 6: Gratitude: +91 94045 32865 thanked Sir for content - "धन्यवाद सर 🙏🏻" - *+91 94045 32865"""

print("Original text:")
print(test_text)
print("\n" + "="*50 + "\n")
print("Cleaned text:")
print(clean_summary_text(test_text))