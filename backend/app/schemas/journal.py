from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JournalEntryBase(BaseModel):
    content: str
    ai_response: Optional[str] = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    ai_response: Optional[str] = None

class JournalEntryResponse(JournalEntryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 