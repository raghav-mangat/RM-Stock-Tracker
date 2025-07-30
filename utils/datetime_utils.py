import pytz
from datetime import datetime

DATETIME_FORMAT = "%m-%d %I:%M %p"
DATE_FORMAT = "%Y-%m-%d"

def polygon_timestamp_et(timestamp, timestamp_type):
    """
    Convert the given polygon timestamp to datetime
    object in Eastern Time (ET).
    :param timestamp:
    :param timestamp_type:
    :return: Datetime object in ET
    """
    factor = None
    if timestamp_type == "nanosecond":
        factor = 1_000_000_000
    elif timestamp_type == "microsecond":
        factor = 1_000_000
    elif timestamp_type == "millisecond":
        factor = 1_000

    eastern_dt = None
    if factor:
        unix_seconds = timestamp / factor

        # Convert to US/Eastern timezone
        eastern_tz = pytz.timezone('US/Eastern')
        eastern_dt = datetime.fromtimestamp(unix_seconds, tz=eastern_tz)

    return eastern_dt

def get_current_et():
    eastern = pytz.timezone("US/Eastern")
    return datetime.now(eastern)

def format_et_datetime(et_datetime):
    """
    Formats datetime in ET into string: 'Friday, Jun 21, 2025, at 08:00PM, ET.'
    """
    return et_datetime.strftime('%A, %b %d, %Y, at %I:%M%p, ET.')

def format_date(date):
    return date.strftime(DATE_FORMAT)
