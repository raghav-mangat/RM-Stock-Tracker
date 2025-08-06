from flask import Flask
from .datetime_utils import format_et_datetime as format_et_datetime_util

def dma_200_perc_diff_color(perc_diff):
    """
    Function to determine stock color based on the percentage
    difference between day closing price and 200 DMA.
    :param perc_diff
    :return: colour - In hex value
    """
    if perc_diff >= 10: # More than 10% above
        color = "#66ff66" # Dark Green
    elif perc_diff <= -10: # More than 10% below
        color = "#FF6666" # Dark Red
    elif perc_diff >= 2: # Between 2% and 10% above
        color = "#99ff99" # Green
    elif perc_diff <= -2:  # Between 2% and 10% below
        color = "#FF9999" # Red
    else: # Within ±2%
        color = "#ffff66" # Yellow
    return color

def stock_change_color(change):
    """
    Function to determine color of the stock based on the change
    in some stock attribute. If the change is greater than or
    equal to 0 then color it green, otherwise color it red.
    :param change
    :return: colour - In hex value
    """
    if change >= 0:
        color = "#00b000" # Dark Green
    else:
        color = "#f00000" # Dark Red
    return color

def humanize_number(num, fallback="N/A", decimals=1):
    """
    Removes the extra zeroes from the given number and returns
    the number with one decimal point precision followed by
    T/B/M/K for Trillion, Billion, Million, or Thousand.
    :return: result - string with compact readable form of the num
    """
    if num is not None and (isinstance(num, int) or isinstance(num, float)):
        result = str(num)
        if num >= 1_000_000_000_000:
            result = f"{num/1_000_000_000_000:.{decimals}f}T"
        elif num >= 1_000_000_000:
            result = f"{num/1_000_000_000:.{decimals}f}B"
        elif num >= 1_000_000:
            result = f"{num/1_000_000:.{decimals}f}M"
        elif num >= 1_000:
            result = f"{num/1_000:.{decimals}f}K"
        else:
            result = f"{num:.{decimals}f}"
    else:
        result = fallback
    return result

def format_et_datetime(et_datetime):
    """
    Formats datetime in ET into string: 'Friday, Jun 21, 2025, at 08:00PM, ET.'
    """
    return format_et_datetime_util(et_datetime)

def display(value, fallback="N/A"):
    """Simple fallback for None values"""
    return value if value is not None else fallback

def format_currency(value, fallback="N/A", decimals=2, prefix="$"):
    """Format as currency with commas and fallback"""
    try:
        return f"{prefix}{value:,.{decimals}f}" if value is not None else fallback
    except (ValueError, TypeError):
        return fallback

def format_float(value, fallback="N/A", decimals=2):
    """Format a float with commas and decimals"""
    try:
        return f"{value:,.{decimals}f}" if value is not None else fallback
    except (ValueError, TypeError):
        return fallback

def format_int(value, fallback="N/A"):
    """Format an integer with commas, no decimals"""
    try:
        return f"{int(value):,}" if value is not None else fallback
    except (ValueError, TypeError):
        return fallback

def format_percent(value, fallback="N/A", decimals=2):
    """Format as percent with fallback"""
    try:
        return f"{value:,.{decimals}f}%" if value is not None else fallback
    except (ValueError, TypeError):
        return fallback

# Register the filters in the Flask app
def register_custom_filters(app: Flask):
    app.jinja_env.filters['dma_200_perc_diff_color'] = dma_200_perc_diff_color
    app.jinja_env.filters['stock_change_color'] = stock_change_color
    app.jinja_env.filters['humanize_number'] = humanize_number
    app.jinja_env.filters['format_et_datetime'] = format_et_datetime
    app.jinja_env.filters['display'] = display
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['float'] = format_float
    app.jinja_env.filters['int'] = format_int
    app.jinja_env.filters['percent'] = format_percent
