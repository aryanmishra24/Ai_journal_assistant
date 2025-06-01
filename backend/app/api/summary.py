from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union
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
    date: Union[str, None] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Get current time in UTC and IST
        current_utc = datetime.utcnow()
        current_ist = to_ist(current_utc)
        
        logger.debug("=== Summary Generation Debug ===")
        logger.debug(f"Received date parameter: {date}")
        
        # Use provided date or today's date in IST
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                logger.debug(f"Parsed target date: {target_date}")
            except ValueError:
                logger.error(f"Invalid date format received: {date}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD."
                )
        else:
            target_date = current_ist.date()
            logger.debug(f"No date provided, using today's date: {target_date}")
            
        logger.debug(f"Current UTC: {current_utc}")
        logger.debug(f"Current IST: {current_ist}")
        logger.debug(f"Target date in IST: {target_date}")
        
        # Convert IST date range to UTC for database query
        target_start_ist = datetime.combine(target_date, datetime.min.time())
        target_end_ist = datetime.combine(target_date, datetime.max.time())
        
        # Convert IST range to UTC for database query
        target_start_utc = target_start_ist - IST_OFFSET
        target_end_utc = target_end_ist - IST_OFFSET
        
        logger.debug("=== Date Range for Query ===")
        logger.debug(f"IST range: {target_start_ist} to {target_end_ist}")
        logger.debug(f"UTC range: {target_start_utc} to {target_end_utc}")
        
        # Get all entries for the user first
        all_entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id
        ).all()
        logger.debug(f"Total entries for user: {len(all_entries)}")
        
        # Log all entries with their timestamps
        logger.debug("=== All Entries ===")
        for entry in all_entries:
            entry_ist = to_ist(entry.created_at)
            logger.debug(f"Entry {entry.id}: UTC={entry.created_at}, IST={entry_ist}")
        
        # Filter entries for the target date
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.created_at >= target_start_utc,
            JournalEntry.created_at <= target_end_utc
        ).all()
        
        # Log the filtered entries
        logger.debug(f"=== Filtered Entries for {target_date} ===")
        logger.debug(f"Found {len(entries)} entries for target date")
        for entry in entries:
            entry_ist = to_ist(entry.created_at)
            logger.debug(f"Entry {entry.id}: UTC={entry.created_at}, IST={entry_ist}")
        
        if not entries:
            logger.info(f"No entries found for user {current_user.id} on {target_date}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entries found for {target_date}."
            )
        
        # Use AI to generate summary
        assistant = AIJournalingAssistant()
        
        # Generate summary using AI with the entries
        summary_text = assistant._generate_daily_summary(db, entries)
        
        # Create new summary with IST date
        summary = DailySummary(
            user_id=current_user.id,
            date=target_date,
            summary=summary_text
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        logger.debug("=== Summary Generated ===")
        logger.debug(f"Summary date: {summary.date}")
        logger.debug(f"Summary text: {summary_text[:200]}...")
        
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