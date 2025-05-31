from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, timedelta
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import get_db
from app.models.journal import DailySummary, JournalEntry
from app.schemas.summary import DailySummaryResponse
from app.utils.auth import get_current_active_user
from app.models.user import User
from app.services.ai import AIJournalingAssistant
from app.utils.timezone import to_ist, IST_OFFSET

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def generate_yesterday_summary_for_user(user_id: int, db: Session):
    """Generate summary for a specific user's yesterday entries"""
    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        # Check if summary already exists
        existing = db.query(DailySummary).filter(
            DailySummary.user_id == user_id,
            DailySummary.date == yesterday
        ).first()
        
        if existing:
            logger.info(f"Summary already exists for user {user_id} on {yesterday}")
            return
        
        # Get yesterday's entries
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= datetime.combine(yesterday, datetime.min.time()),
            JournalEntry.created_at <= datetime.combine(yesterday, datetime.max.time())
        ).all()
        
        if not entries:
            logger.info(f"No entries found for user {user_id} on {yesterday}")
            return
        
        # Generate summary
        assistant = AIJournalingAssistant()
        summary_text = assistant._generate_daily_summary(db, entries)
        
        # Create new summary
        summary = DailySummary(
            user_id=user_id,
            date=yesterday,
            summary=summary_text
        )
        db.add(summary)
        db.commit()
        logger.info(f"Generated summary for user {user_id} on {yesterday}")
        
    except Exception as e:
        logger.error(f"Error generating summary for user {user_id}: {str(e)}", exc_info=True)

def generate_summaries_for_all_users():
    """Generate summaries for all users at the end of the day"""
    try:
        db = next(get_db())
        users = db.query(User).all()
        for user in users:
            generate_yesterday_summary_for_user(user.id, db)
    except Exception as e:
        logger.error(f"Error in scheduled summary generation: {str(e)}", exc_info=True)

# Schedule the task to run at midnight UTC
scheduler.add_job(
    generate_summaries_for_all_users,
    CronTrigger(hour=0, minute=0),
    id='daily_summary_generation'
)

@router.post("/generate", response_model=DailySummaryResponse)
def generate_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get current time in UTC and IST
        current_utc = datetime.utcnow()
        current_ist = to_ist(current_utc)
        
        # Get today's date in IST
        today_ist = current_ist.date()
        logger.debug(f"Current UTC: {current_utc}, Current IST: {current_ist}")
        logger.debug(f"Today's date in IST: {today_ist}")
        
        # Check if summary already exists for today
        existing = db.query(DailySummary).filter(
            DailySummary.user_id == current_user.id,
            DailySummary.date == today_ist
        ).first()
        
        if existing:
            return existing
        
        # Convert IST date range to UTC for database query
        today_start_ist = datetime.combine(today_ist, datetime.min.time())
        today_end_ist = datetime.combine(today_ist, datetime.max.time())
        
        # Convert IST range to UTC for database query
        today_start_utc = today_start_ist - IST_OFFSET
        today_end_utc = today_end_ist - IST_OFFSET
        
        logger.debug(f"Searching for entries between:")
        logger.debug(f"IST range: {today_start_ist} to {today_end_ist}")
        logger.debug(f"UTC range: {today_start_utc} to {today_end_utc}")
        
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.created_at >= today_start_utc,
            JournalEntry.created_at <= today_end_utc
        ).all()
        
        # Log the entries found
        logger.debug(f"Found {len(entries)} entries for today")
        for entry in entries:
            entry_ist = to_ist(entry.created_at)
            logger.debug(f"Entry {entry.id} created at UTC: {entry.created_at}, IST: {entry_ist}")
        
        if not entries:
            logger.info(f"No entries found for user {current_user.id} on {today_ist}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No entries found for today."
            )
        
        # Use AI to generate summary
        assistant = AIJournalingAssistant()
        
        # Generate summary using AI with the entries
        summary_text = assistant._generate_daily_summary(db, entries)
        
        # Create new summary with IST date
        summary = DailySummary(
            user_id=current_user.id,
            date=today_ist,
            summary=summary_text
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily summary: {str(e)}"
        )

@router.get("/", response_model=List[DailySummaryResponse])
def list_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        summaries = db.query(DailySummary).filter(
            DailySummary.user_id == current_user.id
        ).order_by(DailySummary.date.desc()).all()
        
        return summaries
    except Exception as e:
        logger.error(f"Error listing summaries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list summaries: {str(e)}"
        )

@router.get("/{summary_date}", response_model=DailySummaryResponse)
def get_summary(
    summary_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        dt = datetime.strptime(summary_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    summary = db.query(DailySummary).filter(
        DailySummary.user_id == current_user.id,
        DailySummary.date == dt
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this date.")
    
    return summary 