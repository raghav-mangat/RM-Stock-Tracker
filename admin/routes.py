from . import admin_bp
from .decorators import admin_required
from .db_user_data import get_admin_dashboard_data
from flask import render_template

"""
Notes:

- The admin blueprint shows the data to only the admin users.
- Admin users have to be created manually in the database, 
    all the users are non-admin by default.
- All the code required for the admin functionality is in the admin 
    blueprint folder except for some imports from the remaining code. 
    We want the admin blueprint code to be totally separate from the
    remaining code for the application.
- The admin routes can only be accessed by admin users by manually 
    entering the url.
- Currently the admin blueprint only has the admin dashboard page 
    which shows data for:
    - Users along with some useful stats.
    - The Daily App Status Database table. 
    - Watchlist along with some useful stats.
    - Stocks along with some useful stats.
"""

@admin_bp.route("", methods=["GET"])
@admin_required
def index():
    users_data, user_stats, watchlist_stats, daily_status = get_admin_dashboard_data()
    return render_template(
        "dashboard.html",
        users_data=users_data,
        user_stats=user_stats,
        watchlist_stats=watchlist_stats,
        daily_status=daily_status
    )
