from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict

class MoodBase(BaseModel):
    mood_score: float = Field(..., ge=1, le=10, description="Mood score from 1 to 10")
    mood_label: str
    notes: Optional[str] = None

class MoodCreate(MoodBase):
    pass

class Mood(MoodBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MoodTrend(BaseModel):
    date: str
    average_mood: float

class MoodStats(BaseModel):
    average_mood: float
    mood_distribution: Dict[str, int]
    mood_trend: List[MoodTrend]

class DailyMoodSummary(BaseModel):
    id: int
    user_id: int
    date: date
    average_mood: float
    mood_distribution: Dict[str, int]
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True 