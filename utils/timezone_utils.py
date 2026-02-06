from datetime import datetime, timezone, timedelta

def get_ist_now():
    """
    Returns the current datetime in India Standard Time (IST).
    IST is UTC + 5:30.
    """
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def to_ist(dt: datetime):
    """
    Converts a datetime object to IST.
    """
    if dt is None:
        return None
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ist_offset)
