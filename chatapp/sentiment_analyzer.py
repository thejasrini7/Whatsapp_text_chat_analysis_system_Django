from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from .config import SENTIMENT_THRESHOLD
from .utils import parse_timestamp

def analyze_sentiment(messages):
    if not messages:
        return {"error": "No messages found"}
    
    vader_analyzer = SentimentIntensityAnalyzer()
    
    sentiment_data = {
        'overall_sentiment': {'positive': 0, 'neutral': 0, 'negative': 0},
        'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},  # Frontend expected format
        'daily_sentiment': {},
        'user_sentiment': {},
        'user_sentiments': {},  # Frontend expected format
        'sentiment_trend': [],
        'emotional_keywords': {'positive': [], 'negative': []},
        'sentiment_scores': [],  # Store raw scores for analysis
        'negative_messages': [],  # For drill-down modal
        'all_messages_with_sentiment': []  # Complete message details with sentiment
    }
    
    positive_keywords = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
        'love', 'like', 'happy', 'pleased', 'satisfied', 'perfect', 
        'awesome', 'brilliant', 'outstanding', 'superb', 'delighted', 
        'thrilled', 'excited', 'grateful', 'blessed', 'yay', 'hooray'
    ]
    
    negative_keywords = [
        'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 
        'angry', 'sad', 'disappointed', 'frustrated', 'upset', 'annoyed', 
        'furious', 'disgusted', 'worried', 'concerned', 'confused',
        'devastated', 'miserable', 'depressed', 'anxious', 'stressed'
    ]
    
    for msg in messages:
        timestamp = parse_timestamp(msg['timestamp'])
        if timestamp:
            date_str = timestamp.strftime('%Y-%m-%d')
            if date_str not in sentiment_data['daily_sentiment']:
                sentiment_data['daily_sentiment'][date_str] = {'positive': 0, 'neutral': 0, 'negative': 0}
        else:
            date_str = 'unknown'
        
        try:
            blob = TextBlob(msg['message'])
            textblob_polarity = blob.sentiment.polarity
            
            vader_scores = vader_analyzer.polarity_scores(msg['message'])
            vader_compound = vader_scores['compound']
            
            combined_polarity = (0.6 * textblob_polarity) + (0.4 * vader_compound)
            
            sentiment_data['sentiment_scores'].append({
                'timestamp': msg['timestamp'],
                'sender': msg['sender'],
                'polarity': combined_polarity
            })
            
            if combined_polarity > SENTIMENT_THRESHOLD:
                sentiment = 'positive'
            elif combined_polarity < -SENTIMENT_THRESHOLD:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Update both old and new formats for compatibility
            sentiment_data['overall_sentiment'][sentiment] += 1
            sentiment_data['sentiment_breakdown'][sentiment] += 1
            sentiment_data['daily_sentiment'][date_str][sentiment] += 1
            
            user = msg['sender']
            if user not in sentiment_data['user_sentiment']:
                sentiment_data['user_sentiment'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiment'][user][sentiment] += 1
            
            # Also update frontend expected format
            if user not in sentiment_data['user_sentiments']:
                sentiment_data['user_sentiments'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiments'][user][sentiment] += 1
            
            # Store complete message info with sentiment
            message_with_sentiment = {
                'timestamp': msg['timestamp'],
                'sender': user,
                'message': msg['message'],
                'sentiment': sentiment,
                'polarity': combined_polarity,
                'date': date_str
            }
            sentiment_data['all_messages_with_sentiment'].append(message_with_sentiment)
            
            # Store negative messages for drill-down
            if sentiment == 'negative':
                # Determine reason using keyword analysis and sentiment scores
                reason = get_negative_reason(msg['message'], vader_scores, combined_polarity)
                
                negative_message_detail = {
                    'timestamp': msg['timestamp'],
                    'sender': user,
                    'message': msg['message'],
                    'polarity': combined_polarity,
                    'date': date_str,
                    'reason': reason,
                    'vader_scores': vader_scores
                }
                sentiment_data['negative_messages'].append(negative_message_detail)
            
            if timestamp:
                sentiment_data['sentiment_trend'].append({
                    'date': date_str,
                    'sentiment': sentiment,
                    'polarity': combined_polarity
                })
            
            text_lower = msg['message'].lower()
            for keyword in positive_keywords:
                if keyword in text_lower:
                    sentences = re.split(r'[.!?]+', msg['message'])
                    context = next((s.strip() for s in sentences if keyword in s.lower()), "")
                    
                    sentiment_data['emotional_keywords']['positive'].append({
                        'keyword': keyword,
                        'message': context,
                        'sender': user,
                        'timestamp': msg['timestamp'],
                        'polarity': combined_polarity
                    })
            
            for keyword in negative_keywords:
                if keyword in text_lower:
                    sentences = re.split(r'[.!?]+', msg['message'])
                    context = next((s.strip() for s in sentences if keyword in s.lower()), "")
                    
                    sentiment_data['emotional_keywords']['negative'].append({
                        'keyword': keyword,
                        'message': context,
                        'sender': user,
                        'timestamp': msg['timestamp'],
                        'polarity': combined_polarity
                    })
        
        except Exception as e:
            # Handle errors by marking as neutral
            sentiment_data['overall_sentiment']['neutral'] += 1
            sentiment_data['sentiment_breakdown']['neutral'] += 1
            if date_str in sentiment_data['daily_sentiment']:
                sentiment_data['daily_sentiment'][date_str]['neutral'] += 1
            
            user = msg['sender']
            if user not in sentiment_data['user_sentiment']:
                sentiment_data['user_sentiment'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiment'][user]['neutral'] += 1
            
            # Also update frontend expected format
            if user not in sentiment_data['user_sentiments']:
                sentiment_data['user_sentiments'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiments'][user]['neutral'] += 1
    
    return sentiment_data

def get_negative_reason(message, vader_scores, combined_polarity):
    """
    Determine why a message was classified as negative
    """
    message_lower = message.lower()
    
    # Check for specific negative indicators
    reasons = []
    
    # Strong negative emotions
    anger_words = ['angry', 'furious', 'rage', 'mad', 'pissed', 'annoyed', 'frustrated', 'irritated']
    sadness_words = ['sad', 'depressed', 'miserable', 'devastated', 'heartbroken', 'crying', 'upset']
    fear_words = ['scared', 'afraid', 'terrified', 'worried', 'anxious', 'nervous', 'concerned']
    disgust_words = ['disgusted', 'sick', 'revolted', 'gross', 'awful', 'terrible', 'horrible']
    
    # Check for emotional categories
    if any(word in message_lower for word in anger_words):
        reasons.append("Contains expressions of anger or frustration")
    if any(word in message_lower for word in sadness_words):
        reasons.append("Contains expressions of sadness or distress")  
    if any(word in message_lower for word in fear_words):
        reasons.append("Contains expressions of fear or anxiety")
    if any(word in message_lower for word in disgust_words):
        reasons.append("Contains expressions of disgust or strong dislike")
    
    # Check for negative phrases
    negative_phrases = ['hate', 'can\'t stand', 'fed up', 'sick of', 'worst', 'terrible', 'awful', 'disaster']
    if any(phrase in message_lower for phrase in negative_phrases):
        reasons.append("Contains strongly negative language")
    
    # Check for complaints
    complaint_indicators = ['complain', 'problem', 'issue', 'wrong', 'broken', 'failed', 'doesn\'t work']
    if any(indicator in message_lower for indicator in complaint_indicators):
        reasons.append("Contains complaints or problem descriptions")
    
    # Check VADER components
    if vader_scores['neg'] > 0.3:
        reasons.append(f"High negative sentiment score ({vader_scores['neg']:.2f})")
    
    # Check for exclamation points (can indicate strong emotion)
    if message.count('!') >= 2:
        reasons.append("Uses multiple exclamation points indicating strong emotion")
        
    # Check for ALL CAPS (shouting)
    if len([word for word in message.split() if word.isupper() and len(word) > 2]) >= 2:
        reasons.append("Contains words in ALL CAPS indicating shouting/anger")
    
    # If no specific reasons found, use general analysis
    if not reasons:
        if combined_polarity < -0.5:
            reasons.append("Strongly negative overall sentiment")
        elif combined_polarity < -0.2:
            reasons.append("Moderately negative sentiment")
        else:
            reasons.append("Slightly negative sentiment based on language analysis")
    
    return "; ".join(reasons)