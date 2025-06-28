from flask import Flask

def stock_color(perc_diff):
    """
    Function to determine stock color based on the percentage
    difference between day closing price and 200 DMA.
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
    app.jinja_env.filters['stock_color'] = stock_color
    app.jinja_env.filters['format_et_datetime'] = format_et_datetime
    app.jinja_env.filters['display'] = display
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['float'] = format_float
    app.jinja_env.filters['int'] = format_int
    app.jinja_env.filters['percent'] = format_percent
