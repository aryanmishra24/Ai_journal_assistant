from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date, timedelta
import logging

from app.database import get_db
from app.models.journal import JournalEntry, DailySummary
from app.schemas.journal import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse
)
from app.schemas.summary import DailySummaryResponse
from app.utils.auth import get_current_active_user
from app.models.user import User
from app.services.ai import AIJournalingAssistant
from app.utils.timezone import to_ist, to_utc, IST_OFFSET

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.debug(f"Creating journal entry for user {current_user.id}")
        logger.debug(f"Entry content: {entry.content[:100]}...")  # Log first 100 chars
        
        # Create entry with current UTC time
        current_time = datetime.utcnow()
        ist_time = to_ist(current_time)
        logger.debug(f"Creating entry at UTC: {current_time}, IST: {ist_time}")
        logger.debug(f"UTC date: {current_time.date()}, IST date: {ist_time.date()}")
        
        db_entry = JournalEntry(
            user_id=current_user.id,
            content=entry.content,
            ai_response=entry.ai_response,
            created_at=current_time  # Store in UTC
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        # Convert created_at to IST for response
        db_entry.created_at = to_ist(db_entry.created_at)
        
        logger.debug(f"Successfully created entry with ID {db_entry.id}")
        logger.debug(f"Entry created_at (UTC): {current_time}, (IST): {db_entry.created_at}")
        return db_entry
    except Exception as e:
        logger.error(f"Error creating journal entry: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journal entry: {str(e)}"
        )

@router.get("/", response_model=List[JournalEntryResponse])
def list_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id
        ).order_by(JournalEntry.created_at.desc()).all()
        
        # Convert all timestamps to IST
        for entry in entries:
            entry.created_at = to_ist(entry.created_at)
            
        return entries
    except Exception as e:
        logger.error(f"Error listing entries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list entries: {str(e)}"
        )

@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        # Convert timestamp to IST
        entry.created_at = to_ist(entry.created_at)
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entry {entry_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entry: {str(e)}"
        )

@router.put("/{entry_id}", response_model=JournalEntryResponse)
def update_entry(
    entry_id: int,
    entry_update: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        if entry_update.content is not None:
            entry.content = entry_update.content
        if entry_update.ai_response is not None:
            entry.ai_response = entry_update.ai_response
            
        db.commit()
        db.refresh(entry)
        
        # Convert timestamp to IST
        entry.created_at = to_ist(entry.created_at)
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating entry {entry_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update entry: {str(e)}"
        )

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        db.delete(entry)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete entry: {str(e)}"
        )

@router.post("/ai", response_model=dict)
async def get_ai_response(
    content: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.debug(f"Generating AI response for user {current_user.id}")
        logger.debug(f"Content: {content['content'][:100]}...")  # Log first 100 chars
        
        assistant = AIJournalingAssistant()
        response = assistant.chat(content["content"], db)
        
        logger.debug(f"Generated response: {response[:100]}...")  # Log first 100 chars
        return {"response": response}
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI response: {str(e)}"
        )

@router.get("/summary", response_model=DailySummaryResponse)
async def get_daily_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.debug(f"Generating daily summary for user {current_user.id}")
        
        # Get current time in IST for logging
        current_time = datetime.utcnow()
        ist_time = to_ist(current_time)
        logger.debug(f"Generating summary at UTC: {current_time}, IST: {ist_time}")
        
        assistant = AIJournalingAssistant()
        summary = assistant.generate_summary(db)
        
        logger.debug(f"Generated summary: {summary[:100]}...")  # Log first 100 chars
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error generating daily summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily summary: {str(e)}"
        ) 