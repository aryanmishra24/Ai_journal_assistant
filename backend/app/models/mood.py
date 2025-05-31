from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mood_score = Column(Float)  # 1-10 scale
    mood_label = Column(String)  # e.g., "Happy", "Sad", "Anxious"
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="moods")

class DailyMoodSummary(Base):
    __tablename__ = "daily_mood_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, index=True)
    average_mood = Column(Float)
    mood_distribution = Column(String)  # JSON string of mood distribution
    summary = Column(String)  # AI-generated summary of the day's moods
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="mood_summaries") 