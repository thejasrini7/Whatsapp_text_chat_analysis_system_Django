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
        'daily_sentiment': {},
        'user_sentiment': {},
        'sentiment_trend': [],
        'emotional_keywords': {'positive': [], 'negative': []},
        'sentiment_scores': []  # Store raw scores for analysis
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
            
            sentiment_data['overall_sentiment'][sentiment] += 1
            sentiment_data['daily_sentiment'][date_str][sentiment] += 1
            
            user = msg['sender']
            if user not in sentiment_data['user_sentiment']:
                sentiment_data['user_sentiment'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiment'][user][sentiment] += 1
            
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
            sentiment_data['overall_sentiment']['neutral'] += 1
            if date_str in sentiment_data['daily_sentiment']:
                sentiment_data['daily_sentiment'][date_str]['neutral'] += 1
            
            user = msg['sender']
            if user not in sentiment_data['user_sentiment']:
                sentiment_data['user_sentiment'][user] = {'positive': 0, 'neutral': 0, 'negative': 0}
            sentiment_data['user_sentiment'][user]['neutral'] += 1
    
    return sentiment_data