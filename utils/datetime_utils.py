import pytz
from datetime import datetime, UTC

DATETIME_FORMAT = "%m-%d %I:%M %p"
DATE_FORMAT = "%Y-%m-%d"

def polygon_timestamp_to_utc_dt(timestamp, timestamp_type):
    """
    Convert the given polygon timestamp to datetime
    object in UTC.
    :param timestamp:
    :param timestamp_type:
    :return: Datetime object in UTC
    """
    factor = None
    if timestamp_type == "nanosecond":
        factor = 1_000_000_000
    elif timestamp_type == "microsecond":
        factor = 1_000_000
    elif timestamp_type == "millisecond":
        factor = 1_000

    utc_dt = None
    if factor:
        unix_seconds = timestamp / factor

        # Convert to UTC datetime
        utc_dt = datetime.fromtimestamp(unix_seconds, tz=UTC)

    return utc_dt

def get_current_utc():
    return datetime.now(UTC)

def convert_to_utc_tz_aware(utc_dt):
    """
    Database stores TZ naive timestamp, so convert it to TZ aware,
    since we know it is a UTC timestamp
    """
    return utc_dt.replace(tzinfo=UTC)

def format_dt_et(utc_dt):
    """
    Formats datetime in UTC into string in ET: 'Saturday, Jun 21, 2025, ET.'
    """

    et_dt = convert_to_et_dt(utc_dt)
    return et_dt.strftime('%A, %b %d, %Y, ET.')

def format_date(date):
    return date.strftime(DATE_FORMAT)

def format_dt_et_extended(utc_dt):
    """
    Formats datetime in UTC into string in ET: 'Saturday, Jun 21, 2025, at 08:00PM, ET.'
    """

    et_dt = convert_to_et_dt(utc_dt)
    return et_dt.strftime('%A, %b %d, %Y, at %I:%M%p, ET.')

def convert_to_et_dt(dt):
    # Fetch the timezone information
    et = pytz.timezone('US/Eastern')

    # Convert to ET
    et_dt = dt.astimezone(et)

    return et_dt
