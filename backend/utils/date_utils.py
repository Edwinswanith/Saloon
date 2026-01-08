"""
IST (Indian Standard Time) Date Utility Functions

This module provides utility functions for converting between IST and UTC
for date filtering purposes. All date-based filters should use these functions
to ensure consistent IST-based filtering.

IST Offset: UTC+5:30 (5 hours 30 minutes)
"""

from datetime import datetime, timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)


def ist_to_utc_start(date_str):
    """
    Convert IST date string (YYYY-MM-DD) to UTC start of day.
    
    Args:
        date_str: Date string in YYYY-MM-DD format (IST date)
    
    Returns:
        datetime: UTC datetime representing start of day in IST
        Example: 2026-01-06 00:00 IST = 2026-01-05 18:30 UTC
    """
    local_date = datetime.strptime(date_str, '%Y-%m-%d')
    # 00:00 IST = 18:30 previous day UTC
    return local_date.replace(hour=0, minute=0, second=0, microsecond=0) - IST_OFFSET


def ist_to_utc_end(date_str):
    """
    Convert IST date string (YYYY-MM-DD) to UTC end of day.
    
    This function handles the case where bills/records are stored at noon IST (06:30 UTC).
    To include all records from the end_date, we extend to next day 06:29:59 UTC.
    
    Args:
        date_str: Date string in YYYY-MM-DD format (IST date)
    
    Returns:
        datetime: UTC datetime representing end of day in IST
        Example: For 2026-01-06, returns 2026-01-07 06:29:59 UTC
                 (which includes bills stored at 2026-01-06 06:30 UTC)
    """
    local_date = datetime.strptime(date_str, '%Y-%m-%d')
    # Bills stored at noon on end_date: 12:00 IST = 06:30 UTC same day
    # To include all bills from end_date, use next day 06:30 UTC (exclusive)
    # Then subtract 1 second to make it inclusive
    end = (local_date + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0) - IST_OFFSET
    return end - timedelta(seconds=1)


def get_ist_date_range(start_date, end_date):
    """
    Get UTC datetime range for IST date range.
    
    Args:
        start_date: Start date string in YYYY-MM-DD format (IST) or None
        end_date: End date string in YYYY-MM-DD format (IST) or None
    
    Returns:
        tuple: (start_utc, end_utc) where both are datetime objects or None
    """
    start = ist_to_utc_start(start_date) if start_date else None
    end = ist_to_utc_end(end_date) if end_date else None
    return start, end


def utc_to_ist_datetime(utc_datetime):
    """
    Convert UTC datetime to IST datetime (for display purposes).
    
    Args:
        utc_datetime: datetime object in UTC
    
    Returns:
        datetime: datetime object in IST
    """
    if utc_datetime is None:
        return None
    return utc_datetime + IST_OFFSET


def get_ist_today():
    """
    Get current date in IST as a date string.
    
    Returns:
        str: Current date in YYYY-MM-DD format (IST)
    """
    utc_now = datetime.utcnow()
    ist_now = utc_now + IST_OFFSET
    return ist_now.strftime('%Y-%m-%d')


def get_ist_date_string(dt):
    """
    Get IST date string from a datetime object.
    
    Args:
        dt: datetime object (assumed to be in UTC)
    
    Returns:
        str: Date in YYYY-MM-DD format (IST)
    """
    if dt is None:
        return None
    ist_dt = dt + IST_OFFSET
    return ist_dt.strftime('%Y-%m-%d')

