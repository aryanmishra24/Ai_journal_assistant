from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class TopicCount(BaseModel):
    topic: str
    count: int

class WordCountTrend(BaseModel):
    date: str
    average_word_count: float

class SentimentTrend(BaseModel):
    date: str
    average_sentiment: float

class JournalStats(BaseModel):
    total_entries: int
    average_entry_length: float
    most_common_topics: List[TopicCount]
    writing_frequency: Dict[str, int]
    word_count_trend: List[WordCountTrend]

class SentimentAnalysis(BaseModel):
    overall_sentiment: float  # -1 to 1 scale
    sentiment_by_topic: Dict[str, float]
    sentiment_trend: List[SentimentTrend]  # Daily sentiment averages

class JournalInsights(BaseModel):
    stats: JournalStats
    sentiment: SentimentAnalysis
    top_keywords: List[str]
    writing_patterns: Dict[str, str]  # e.g., "Most active time": "Morning"
    recommendations: List[str]  # AI-generated writing suggestions 