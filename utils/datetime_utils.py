import pytz
from datetime import datetime, UTC

DATETIME_FORMAT = "%m-%d %I:%M %p"
DATE_FORMAT = "%Y-%m-%d"

# 'Friday, Jan 16, 2026 · 10:34 AM, ET'
DATETIME_ET_FORMAT = "%A, %b %d, %Y · %I:%M %p, ET"

def polygon_timestamp_to_utc_dt(timestamp, timestamp_type):
    """
    Convert the given polygon timestamp to datetime
    object in UTC.
    :param timestamp:
    :param timestamp_type:
    :return: Datetime object in UTC
    """
    factor = get_polygon_timestamp_conversion_factor(timestamp_type)

    utc_dt = None
    if factor:
        unix_seconds = timestamp / factor

        # Convert to UTC datetime
        utc_dt = datetime.fromtimestamp(unix_seconds, tz=UTC)

    return utc_dt

def utc_dt_to_polygon_timestamp(utc_dt, timestamp_type):
    factor = get_polygon_timestamp_conversion_factor(timestamp_type)

    timestamp = None
    if factor:
        unix_seconds = utc_dt.timestamp()

        # Convert to Polygon timestamp
        timestamp = int(unix_seconds * factor)

    return timestamp

def get_polygon_timestamp_conversion_factor(timestamp_type):
    factor = None
    if timestamp_type == "nanosecond":
        factor = 1_000_000_000
    elif timestamp_type == "microsecond":
        factor = 1_000_000
    elif timestamp_type == "millisecond":
        factor = 1_000
    return factor

def get_current_utc():
    return datetime.now(UTC)

def get_current_utc_date():
    return datetime.now(UTC).date()

def convert_to_utc_tz_aware(utc_dt):
    """
    Database stores TZ naive timestamp, so convert it to TZ aware,
    since we know it is a UTC timestamp
    """
    return utc_dt.replace(tzinfo=UTC)

def format_dt_et(utc_dt):
    """
    Formats datetime in UTC into string in ET
    """

    et_dt = convert_to_et_dt(utc_dt)
    return et_dt.strftime(DATETIME_ET_FORMAT)

def format_date_et(utc_dt):
    """
    Formats datetime in UTC into date string in ET
    """

    et_dt = convert_to_et_dt(utc_dt)
    return format_date(et_dt)

def format_date(date):
    return date.strftime(DATE_FORMAT)

def convert_to_et_dt(dt):
    # Fetch the timezone information
    et = pytz.timezone('US/Eastern')

    # Convert to ET
    et_dt = dt.astimezone(et)

    return et_dt

def get_dt_from_et_dt_str(et_dt_str):
    # Parse the string into a datetime object
    dt = datetime.strptime(et_dt_str, DATETIME_ET_FORMAT)

    return dt