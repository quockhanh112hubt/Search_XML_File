"""
Date utilities for parsing and formatting
"""

from datetime import datetime, timedelta
from typing import Tuple

def parse_date_range(range_text: str) -> Tuple[datetime, datetime]:
    """Parse date range text into start and end dates"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if range_text == "Today":
        return today, today
    elif range_text == "Yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif range_text == "This Week":
        start = today - timedelta(days=today.weekday())
        return start, today
    elif range_text == "Last Week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end
    elif range_text == "This Month":
        start = today.replace(day=1)
        return start, today
    elif range_text == "Last Month":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start, last_month_end
    elif range_text == "Last 7 Days":
        start = today - timedelta(days=6)
        return start, today
    elif range_text == "Last 30 Days":
        start = today - timedelta(days=29)
        return start, today
    else:
        # Default to today
        return today, today

def format_date_for_display(date: datetime) -> str:
    """Format date for display in UI"""
    return date.strftime("%Y-%m-%d")

def format_date_for_ftp(date: datetime) -> str:
    """Format date for FTP directory name"""
    return date.strftime("%Y%m%d")
