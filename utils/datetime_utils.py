def format_et_datetime(et_datetime):
    """
    Formats datetime in ET into string: 'Friday, Jun 21, 2025, at 08:00PM, ET.'
    """
    return et_datetime.strftime('%A, %b %d, %Y, at %I:%M%p, ET.')