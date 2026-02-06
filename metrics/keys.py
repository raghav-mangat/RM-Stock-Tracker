from datetime import date
from utils.datetime_utils import get_current_utc_date, format_date


def metrics_dated_key(metric_name: str, utc_date: date | None = None) -> str:
    """
    Build a Redis key for a metric for a specific UTC date.
    """
    if utc_date is None:
        utc_date = get_current_utc_date()

    date_str = format_date(utc_date)  # YYYY-MM-DD
    return f"metrics:{date_str}:{metric_name}"