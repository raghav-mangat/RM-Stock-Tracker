def stock_color(perc_diff):
    """
    Function to determine stock color based on the percentage
    difference between last closing price and 200 DMA.
    :param perc_diff:
    :return: colour.
    """
    if perc_diff >= 10: # More than 10% above
        return "#66ff66" # Dark Green
    elif perc_diff <= -10: # More than 10% below
        return "#FF6666" # Dark Red
    elif perc_diff >= 2: # Between 2% and 10% above
        return "#99ff99" # Green
    elif perc_diff <= -2:  # Between 2% and 10% below
        return "#FF9999" # Red
    else: # Within ±2%
        return "#ffff66" # Yellow

def format_et_datetime(et_datetime):
    """
    Formats datetime in ET into string: 'Friday, Jun 21, 2025, at 08:00PM, ET.'
    """
    return et_datetime.strftime('%A, %b %d, %Y, at %I:%M%p, ET.')