from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo


def get_timezone(tz: str = "Africa/Lagos") -> ZoneInfo:
    """Get timezone object"""
    return ZoneInfo(tz)


def get_timeaware(dateobj: datetime, timez: str = "Africa/Lagos") -> datetime:
    """Convert datetime to timezone-aware datetime"""
    tz = get_timezone(timez)
    return dateobj.astimezone(tz)


def get_current_timezone(timez: str = "Africa/Lagos") -> datetime:
    """Get current time in specified timezone"""
    tz = get_timezone(timez)
    return datetime.now(tz)


def get_year_range(timez: str = "Africa/Lagos") -> Tuple[datetime, datetime]:
    """Get start and end of current year in specified timezone"""
    now = get_current_timezone(timez)
    start = now.replace(month=1, day=1, hour=0, minute=0,
                        second=0, microsecond=0)
    stop = now.replace(month=12, day=31, hour=23, minute=59,
                       second=59, microsecond=999999)
    return start, stop


def get_month_range(year: int, month: int, timez: str = "Africa/Lagos") -> Tuple[datetime, datetime]:
    """Get start and end of specified month"""
    import calendar

    tz = get_timezone(timez)
    dt = datetime.now(tz)
    _, last_day = calendar.monthrange(year, month)

    start = dt.replace(year=year, month=month, day=1, hour=0,
                       minute=0, second=0, microsecond=0)
    end = dt.replace(year=year, month=month, day=last_day,
                     hour=23, minute=59, second=59, microsecond=999999)

    return start, end


def date_format(date_obj: datetime, strft: str = '%H:%M:%S', tz_enabled: bool = False, timez: str = "Africa/Lagos") -> str:
    """Format datetime for display based on how recent it is"""
    now = datetime.now()

    if tz_enabled:
        now = get_timeaware(now, timez)

    diff = now - date_obj

    if diff.days == 0:
        return date_obj.strftime(strft)
    elif diff.days == 1:
        return 'Yesterday'
    elif 1 < diff.days < 10:
        return date_obj.strftime('%d, %B')
    else:
        return date_obj.strftime("%d-%m-%Y")
