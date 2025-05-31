from datetime import datetime, timedelta

# IST timezone offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)

def to_ist(utc_time: datetime) -> datetime:
    """Convert UTC time to IST"""
    return utc_time + IST_OFFSET

def to_utc(ist_time: datetime) -> datetime:
    """Convert IST time to UTC"""
    return ist_time - IST_OFFSET 