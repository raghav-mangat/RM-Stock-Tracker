from datetime import datetime, UTC
from utils.status_files import get_market_status

def get_market_status_with_time_ago():
    market_status = get_market_status()

    if market_status:
        market_status["time_ago"] = format_time_ago(
            market_status.get("timestamp")
        )

    return market_status

def format_time_ago(timestamp_str: str) -> str:
    """
    Keep this consistent with the front-end version written
    in JS.
    """

    if not timestamp_str:
        return ""

    updated = datetime.fromisoformat(timestamp_str)

    # Ensure timezone-aware
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    diff = now - updated

    diff_sec = int(diff.total_seconds())
    diff_min = diff_sec // 60

    if diff_sec < 10:
        return "Updated just now"
    if diff_sec < 60:
        return f"Updated {diff_sec}s ago"
    if diff_min == 1:
        return "Updated 1 min ago"
    if diff_min < 60:
        return f"Updated {diff_min} min ago"

    diff_hr = diff_min // 60
    if diff_hr == 1:
        return "Updated 1 hr ago"
    if diff_hr < 24:
        return f"Updated {diff_hr} hr ago"

    diff_day = diff_hr // 24
    return f"Updated {diff_day} day{'s' if diff_day > 1 else ''} ago"