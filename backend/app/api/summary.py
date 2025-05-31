from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date

from app.database import get_db
from app.models.journal import DailySummary, JournalEntry
from app.schemas.summary import DailySummaryResponse
from app.utils.auth import get_current_active_user
from app.models.user import User
from app.services.ai import AIJournalingAssistant

router = APIRouter()

@router.post("/generate", response_model=DailySummaryResponse)
def generate_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    today = date.today()
    # Get all today's entries for the user
    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.created_at >= datetime.combine(today, datetime.min.time()),
        JournalEntry.created_at <= datetime.combine(today, datetime.max.time())
    ).all()
    
    if not entries:
        raise HTTPException(status_code=404, detail="No entries for today.")
    
    try:
        # Use AI to generate summary
        assistant = AIJournalingAssistant()
        
        # Generate summary using AI with the entries
        summary_text = assistant._generate_daily_summary(db, entries)
        
        # Check if summary already exists
        existing = db.query(DailySummary).filter(
            DailySummary.user_id == current_user.id,
            DailySummary.date == today
        ).first()
        
        if existing:
            existing.summary = summary_text
            db.commit()
            db.refresh(existing)
            return existing
            
        summary = DailySummary(
            user_id=current_user.id,
            date=today,
            summary=summary_text
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

@router.get("/", response_model=List[DailySummaryResponse])
def list_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(DailySummary).filter(DailySummary.user_id == current_user.id).order_by(DailySummary.date.desc()).all()

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