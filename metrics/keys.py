from datetime import datetime
from utils.datetime_utils import get_current_utc, format_date


def metrics_dated_key(metric_name: str, dt: datetime | None = None) -> str:
    """
    Build a Redis key for a metric for a specific UTC date.
    """
    if dt is None:
        dt = get_current_utc()

    date_str = format_date(dt)  # YYYY-MM-DD
    return f"metrics:{date_str}:{metric_name}"