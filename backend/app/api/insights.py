from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict
from app.database import get_db
from app.models.journal import JournalEntry
from app.schemas.insights import JournalInsights, JournalStats, SentimentAnalysis
from app.utils.auth import get_current_user
from app.models.user import User
from textblob import TextBlob
from collections import Counter
import re

router = APIRouter()

def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text using TextBlob."""
    return TextBlob(text).sentiment.polarity

def extract_topics(text: str) -> List[str]:
    """Extract main topics from text using simple keyword extraction."""
    # Remove common words and get word frequencies
    words = re.findall(r'\w+', text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as'}
    words = [w for w in words if w not in stop_words and len(w) > 3]
    return [word for word, _ in Counter(words).most_common(5)]

@router.get("/stats", response_model=JournalStats)
def get_journal_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all entries within the date range
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= start_date
    ).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No journal entries found for the specified period")
    
    # Calculate basic stats
    total_entries = len(entries)
    total_words = sum(len(entry.content.split()) for entry in entries)
    average_entry_length = total_words / total_entries if total_entries > 0 else 0
    
    # Calculate writing frequency by day of week
    writing_frequency = {}
    for entry in entries:
        day = entry.created_at.strftime('%A')
        writing_frequency[day] = writing_frequency.get(day, 0) + 1
    
    # Calculate word count trend
    word_count_trend = []
    current_date = start_date
    while current_date <= datetime.utcnow():
        daily_entries = [e for e in entries if e.created_at.date() == current_date.date()]
        if daily_entries:
            daily_word_count = sum(len(e.content.split()) for e in daily_entries) / len(daily_entries)
            word_count_trend.append({
                "date": current_date.date().isoformat(),
                "average_word_count": daily_word_count
            })
        current_date += timedelta(days=1)
    
    # Extract most common topics
    all_topics = []
    for entry in entries:
        all_topics.extend(extract_topics(entry.content))
    most_common_topics = [{"topic": topic, "count": count} 
                         for topic, count in Counter(all_topics).most_common(10)]
    
    return JournalStats(
        total_entries=total_entries,
        average_entry_length=average_entry_length,
        most_common_topics=most_common_topics,
        writing_frequency=writing_frequency,
        word_count_trend=word_count_trend
    )

@router.get("/sentiment", response_model=SentimentAnalysis)
def get_sentiment_analysis(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= start_date
    ).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No journal entries found for the specified period")
    
    # Calculate overall sentiment
    sentiments = [analyze_sentiment(entry.content) for entry in entries]
    overall_sentiment = sum(sentiments) / len(sentiments)
    
    # Calculate sentiment by topic
    sentiment_by_topic = {}
    for entry in entries:
        topics = extract_topics(entry.content)
        sentiment = analyze_sentiment(entry.content)
        for topic in topics:
            if topic not in sentiment_by_topic:
                sentiment_by_topic[topic] = []
            sentiment_by_topic[topic].append(sentiment)
    
    # Average sentiment by topic
    sentiment_by_topic = {
        topic: sum(sentiments) / len(sentiments)
        for topic, sentiments in sentiment_by_topic.items()
    }
    
    # Calculate sentiment trend
    sentiment_trend = []
    current_date = start_date
    while current_date <= datetime.utcnow():
        daily_entries = [e for e in entries if e.created_at.date() == current_date.date()]
        if daily_entries:
            daily_sentiment = sum(analyze_sentiment(e.content) for e in daily_entries) / len(daily_entries)
            sentiment_trend.append({
                "date": current_date.date().isoformat(),
                "average_sentiment": daily_sentiment
            })
        current_date += timedelta(days=1)
    
    return SentimentAnalysis(
        overall_sentiment=overall_sentiment,
        sentiment_by_topic=sentiment_by_topic,
        sentiment_trend=sentiment_trend
    )

@router.get("/insights", response_model=JournalInsights)
def get_journal_insights(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get stats and sentiment analysis
    stats = get_journal_stats(days, db, current_user)
    sentiment = get_sentiment_analysis(days, db, current_user)
    
    # Get entries for additional analysis
    start_date = datetime.utcnow() - timedelta(days=days)
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= start_date
    ).all()
    
    # Extract top keywords
    all_words = []
    for entry in entries:
        all_words.extend(extract_topics(entry.content))
    top_keywords = [word for word, _ in Counter(all_words).most_common(10)]
    
    # Analyze writing patterns
    writing_patterns = {}
    if entries:
        # Most active time of day
        times = [entry.created_at.hour for entry in entries]
        most_common_hour = max(set(times), key=times.count)
        if 5 <= most_common_hour < 12:
            writing_patterns["Most active time"] = "Morning"
        elif 12 <= most_common_hour < 17:
            writing_patterns["Most active time"] = "Afternoon"
        elif 17 <= most_common_hour < 22:
            writing_patterns["Most active time"] = "Evening"
        else:
            writing_patterns["Most active time"] = "Night"
        
        # Writing consistency
        days_with_entries = len(set(entry.created_at.date() for entry in entries))
        writing_patterns["Writing consistency"] = f"{days_with_entries} days out of {days}"
    
    # Generate recommendations
    recommendations = []
    if stats.average_entry_length < 100:
        recommendations.append("Try writing longer entries to capture more details")
    if stats.total_entries < 10:
        recommendations.append("Consider journaling more frequently to build a better habit")
    if sentiment.overall_sentiment < -0.2:
        recommendations.append("Your recent entries show some negative sentiment. Consider focusing on positive aspects")
    
    return JournalInsights(
        stats=stats,
        sentiment=sentiment,
        top_keywords=top_keywords,
        writing_patterns=writing_patterns,
        recommendations=recommendations
    ) 