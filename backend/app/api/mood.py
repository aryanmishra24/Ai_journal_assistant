from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import logging
from app.database import get_db
from app.models.mood import Mood
from app.schemas.mood import MoodCreate, Mood as MoodSchema, MoodStats
from app.utils.auth import get_current_user
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# IST timezone offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)

def to_ist(utc_time: datetime) -> datetime:
    """Convert UTC time to IST"""
    return utc_time + IST_OFFSET

router = APIRouter()

@router.post("/", response_model=MoodSchema)
def create_mood(
    mood: MoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug(f"Creating mood entry for user {current_user.id}")
        logger.debug(f"Mood score: {mood.mood_score}, Label: {mood.mood_label}")
        
        # Create mood entry with current UTC time
        current_time = datetime.utcnow()
        ist_time = to_ist(current_time)
        logger.debug(f"Creating mood at UTC: {current_time}, IST: {ist_time}")
        
        db_mood = Mood(
            user_id=current_user.id,
            mood_score=mood.mood_score,
            mood_label=mood.mood_label,
            notes=mood.notes,
            created_at=current_time  # Store in UTC
        )
        db.add(db_mood)
        db.commit()
        db.refresh(db_mood)
        
        # Convert created_at to IST for response
        db_mood.created_at = to_ist(db_mood.created_at)
        
        logger.debug(f"Successfully created mood entry with ID {db_mood.id}")
        return db_mood
    except Exception as e:
        logger.error(f"Error creating mood entry: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mood entry: {str(e)}"
        )

@router.get("/", response_model=List[MoodSchema])
def get_moods(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug(f"Getting moods for user {current_user.id} (skip={skip}, limit={limit})")
        
        moods = db.query(Mood).filter(
            Mood.user_id == current_user.id
        ).order_by(Mood.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert all timestamps to IST
        for mood in moods:
            mood.created_at = to_ist(mood.created_at)
        
        logger.debug(f"Retrieved {len(moods)} mood entries")
        return moods
    except Exception as e:
        logger.error(f"Error getting moods: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get moods: {str(e)}"
        )

@router.get("/stats", response_model=MoodStats)
def get_mood_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug(f"Getting mood stats for user {current_user.id} (days={days})")
        
        # Calculate start date in UTC
        start_date = datetime.utcnow() - timedelta(days=days)
        logger.debug(f"Stats period: {to_ist(start_date)} to {to_ist(datetime.utcnow())} IST")
        
        # Get all moods within the date range
        moods = db.query(Mood).filter(
            Mood.user_id == current_user.id,
            Mood.created_at >= start_date
        ).all()
        
        if not moods:
            logger.debug("No mood data found for the specified period")
            raise HTTPException(status_code=404, detail="No mood data found for the specified period")
        
        # Calculate average mood
        average_mood = sum(mood.mood_score for mood in moods) / len(moods)
        
        # Calculate mood distribution
        mood_distribution = {}
        for mood in moods:
            mood_distribution[mood.mood_label] = mood_distribution.get(mood.mood_label, 0) + 1
        
        # Calculate mood trend (daily averages)
        mood_trend = []
        current_date = start_date
        while current_date <= datetime.utcnow():
            # Convert current_date to IST for comparison
            current_date_ist = to_ist(current_date)
            daily_moods = [m for m in moods if to_ist(m.created_at).date() == current_date_ist.date()]
            if daily_moods:
                daily_avg = sum(m.mood_score for m in daily_moods) / len(daily_moods)
                mood_trend.append({
                    "date": current_date_ist.date().isoformat(),
                    "average_mood": daily_avg
                })
            current_date += timedelta(days=1)
        
        logger.debug(f"Generated stats: avg={average_mood}, distribution={mood_distribution}")
        return MoodStats(
            average_mood=average_mood,
            mood_distribution=mood_distribution,
            mood_trend=mood_trend
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mood stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mood stats: {str(e)}"
        )

@router.delete("/{mood_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mood(
    mood_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug(f"Deleting mood entry {mood_id} for user {current_user.id}")
        
        mood = db.query(Mood).filter(Mood.id == mood_id, Mood.user_id == current_user.id).first()
        if not mood:
            logger.debug(f"Mood entry {mood_id} not found")
            raise HTTPException(status_code=404, detail="Mood entry not found")
            
        db.delete(mood)
        db.commit()
        
        logger.debug(f"Successfully deleted mood entry {mood_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mood entry: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete mood entry: {str(e)}"
        ) 