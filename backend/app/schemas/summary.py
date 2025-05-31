from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DailySummaryBase(BaseModel):
    date: datetime
    summary: str

class DailySummaryCreate(DailySummaryBase):
    pass

class DailySummaryResponse(DailySummaryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 