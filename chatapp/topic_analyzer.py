from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
from .config import TOPIC_MIN_WORD_LENGTH, TOPIC_MAX_TOPICS

def extract_topics(messages, top_n=5):

    stopwords = set([
        'the', 'is', 'in', 'and', 'to', 'a', 'of', 'for', 'on', 'with', 'at', 'by', 'an', 'be', 
        'this', 'that', 'it', 'as', 'are', 'was', 'from', 'or', 'but', 'not', 'have', 'has', 'had', 
        'you', 'i', 'we', 'they', 'he', 'she', 'his', 'her', 'them', 'our', 'your', 'my', 'me', 
        'so', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'about', 'just', 
        'if', 'then', 'than', 'too', 'very', 'all', 'any', 'some', 'no', 'yes', 'one', 'two', 
        'up', 'down', 'out', 'over', 'under', 'again', 'more', 'most', 'such', 'only', 'own', 
        'same', 'other', 'new', 'now', 'after', 'before', 'because', 'how', 'when', 'where', 
        'who', 'what', 'which', 'why', 'whom', 'whose', 'been', 'being', 'into', 'during', 
        'while', 'through', 'each', 'few', 'many', 'much', 'every', 'both', 'either', 'neither', 
        'between', 'among', 'against', 'per', 'via', 'like', 'unlike', 'within', 'without', 
        'across', 'toward', 'upon', 'off', 'onto', 'beside', 'besides', 'along', 'around', 
        'behind', 'beyond', 'despite', 'except', 'inside', 'outside', 'past', 'since', 'until', 
        'upon', 'via', 'within', 'without'
    ])

    processed_messages = []
    for msg in messages:
        text = msg.get('message', '').lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'[^a-z ]', ' ', text)
        processed_messages.append(text)

    all_text = ' '.join(processed_messages)
    words = [word for word in all_text.split() if word not in stopwords and len(word) > TOPIC_MIN_WORD_LENGTH]

    vectorizer = TfidfVectorizer(max_features=1000, stop_words=list(stopwords))
    tfidf_matrix = vectorizer.fit_transform(processed_messages)
    feature_names = vectorizer.get_feature_names_out()
    
    tfidf_scores = tfidf_matrix.sum(axis=0).A1
    tfidf_keywords = sorted(zip(feature_names, tfidf_scores), key=lambda x: x[1], reverse=True)
    
    if len(processed_messages) > 10:
        lda = LatentDirichletAllocation(n_components=min(top_n, TOPIC_MAX_TOPICS), random_state=42)
        lda.fit(tfidf_matrix)
        
        lda_topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-6:-1]]
            lda_topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weight': float(topic.sum())
            })
    else:
        lda_topics = []
    
    topics = []
    
    # Add TF-IDF keywords
    for i, (keyword, score) in enumerate(tfidf_keywords[:top_n]):
        examples = []
        for msg in messages:
            if keyword in msg.get('message', '').lower():
                examples.append({
                    'sender': msg['sender'],
                    'timestamp': msg['timestamp'],
                    'message': msg['message'][:100] + '...' if len(msg['message']) > 100 else msg['message']
                })
                if len(examples) >= 2: 
                    break
        
        topics.append({
            'topic': keyword,
            'method': 'tfidf',
            'score': float(score),
            'examples': examples
        })
    
    # Add LDA topics
    for topic in lda_topics:
        examples = []
        topic_words = set(topic['words'])
        for msg in messages:
            msg_words = set(msg.get('message', '').lower().split())
            if topic_words.intersection(msg_words):
                examples.append({
                    'sender': msg['sender'],
                    'timestamp': msg['timestamp'],
                    'message': msg['message'][:100] + '...' if len(msg['message']) > 100 else msg['message']
                })
                if len(examples) >= 2:  
                    break
        topics.append({
            'topic': ', '.join(topic['words']),
            'method': 'lda',
            'score': topic['weight'],
            'examples': examples
        })

    topics = sorted(topics, key=lambda x: x['score'], reverse=True)
    return topics[:top_n]