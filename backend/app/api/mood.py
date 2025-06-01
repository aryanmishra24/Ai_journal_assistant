from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from datetime import datetime, timedelta, date
import json
import logging
from app.database import get_db
from app.models.mood import Mood, DailyMoodSummary
from app.schemas.mood import MoodCreate, Mood as MoodSchema, MoodStats, DailyMoodSummary as DailyMoodSummarySchema
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.ai import AIJournalingAssistant
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# IST timezone offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)

def to_ist(utc_time: datetime) -> datetime:
    """Convert UTC time to IST"""
    return utc_time + IST_OFFSET

router = APIRouter()

class SummaryRequest(BaseModel):
    date: Optional[str] = None

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
        
        # Delete any existing summary for this date
        mood_date = to_ist(current_time).date()
        existing_summary = db.query(DailyMoodSummary).filter(
            DailyMoodSummary.user_id == current_user.id,
            DailyMoodSummary.date == mood_date
        ).first()
        if existing_summary:
            db.delete(existing_summary)
            db.commit()
            logger.debug(f"Deleted existing summary for {mood_date}")
        
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
        
        # Get today's summary if it exists
        today = date.today()
        today_summary = db.query(DailyMoodSummary).filter(
            DailyMoodSummary.user_id == current_user.id,
            DailyMoodSummary.date == today
        ).first()
        
        summary = today_summary.summary if today_summary else None
        
        logger.debug(f"Generated stats: avg={average_mood}, distribution={mood_distribution}")
        return MoodStats(
            average_mood=average_mood,
            mood_distribution=mood_distribution,
            mood_trend=mood_trend,
            summary=summary
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
        
        # Get the date of the mood entry before deleting it
        mood_date = to_ist(mood.created_at).date()
            
        db.delete(mood)
        db.commit()
        
        # Delete any existing summary for this date
        existing_summary = db.query(DailyMoodSummary).filter(
            DailyMoodSummary.user_id == current_user.id,
            DailyMoodSummary.date == mood_date
        ).first()
        if existing_summary:
            db.delete(existing_summary)
            db.commit()
            logger.debug(f"Deleted existing summary for {mood_date}")
        
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

@router.post("/summary/generate", response_model=DailyMoodSummarySchema)
def generate_daily_mood_summary(
    request: SummaryRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Get current time in UTC and IST
        current_utc = datetime.utcnow()
        current_ist = to_ist(current_utc)
        
        # Use provided date or today's date in IST
        if request.date:
            try:
                target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
                logger.debug(f"Using provided date: {request.date}, parsed as: {target_date}")
            except ValueError:
                logger.error(f"Invalid date format received: {request.date}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD."
                )
        else:
            target_date = current_ist.date()
            logger.debug(f"No date provided, using today's date: {target_date}")
            
        logger.debug(f"Current UTC: {current_utc}, Current IST: {current_ist}")
        logger.debug(f"Target date in IST: {target_date}")
        
        # Convert IST date range to UTC for database query
        target_start_ist = datetime.combine(target_date, datetime.min.time())
        target_end_ist = datetime.combine(target_date, datetime.max.time())
        
        # Convert IST range to UTC for database query
        target_start_utc = target_start_ist - IST_OFFSET
        target_end_utc = target_end_ist - IST_OFFSET
        
        logger.debug(f"Searching for moods between:")
        logger.debug(f"IST range: {target_start_ist} to {target_end_ist}")
        logger.debug(f"UTC range: {target_start_utc} to {target_end_utc}")
        
        # Filter moods for the target date
        moods = db.query(Mood).filter(
            Mood.user_id == current_user.id,
            Mood.created_at >= target_start_utc,
            Mood.created_at <= target_end_utc
        ).all()
        
        # Log the moods found
        logger.debug(f"Found {len(moods)} moods for target date")
        for mood in moods:
            mood_ist = to_ist(mood.created_at)
            logger.debug(f"Mood {mood.id} created at UTC: {mood.created_at}, IST: {mood_ist}")
        
        if not moods:
            logger.info(f"No moods found for user {current_user.id} on {target_date}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No moods found for {target_date}."
            )
        
        # Delete any existing summary for this date
        existing_summary = db.query(DailyMoodSummary).filter(
            DailyMoodSummary.user_id == current_user.id,
            DailyMoodSummary.date == target_date
        ).first()
        if existing_summary:
            db.delete(existing_summary)
            db.commit()
            logger.debug(f"Deleted existing summary for {target_date}")
        
        # Use AI to generate summary
        assistant = AIJournalingAssistant()
        
        # Generate summary using AI with the moods
        summary_text = assistant.generate_mood_summary(moods)
        
        # Calculate average mood and distribution
        average_mood = sum(mood.mood_score for mood in moods) / len(moods)
        mood_distribution = {}
        for mood in moods:
            mood_distribution[mood.mood_label] = mood_distribution.get(mood.mood_label, 0) + 1
        
        # Create new summary with IST date
        summary = DailyMoodSummary(
            user_id=current_user.id,
            date=target_date,
            average_mood=average_mood,
            mood_distribution=json.dumps(mood_distribution),
            summary=summary_text
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        # Convert mood_distribution from JSON string to dict for response
        summary.mood_distribution = json.loads(summary.mood_distribution)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mood summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mood summary: {str(e)}"
        )

@router.get("/summary", response_model=List[DailyMoodSummarySchema])
def list_mood_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        summaries = db.query(DailyMoodSummary).filter(
            DailyMoodSummary.user_id == current_user.id
        ).order_by(DailyMoodSummary.date.desc()).all()
        
        # Convert mood_distribution from JSON string to dict
        for summary in summaries:
            summary.mood_distribution = json.loads(summary.mood_distribution)
        
        return summaries
    except Exception as e:
        logger.error(f"Error listing mood summaries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list mood summaries: {str(e)}"
        )

@router.get("/summary/{summary_date}", response_model=DailyMoodSummarySchema)
def get_mood_summary(
    summary_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        dt = datetime.strptime(summary_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    summary = db.query(DailyMoodSummary).filter(
        DailyMoodSummary.user_id == current_user.id,
        DailyMoodSummary.date == dt
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this date.")
    
    # Convert mood_distribution from JSON string to dict
    summary.mood_distribution = json.loads(summary.mood_distribution)
    
    return summary 