from datetime import datetime, timedelta
from sqlalchemy.sql.functions import count, func
from models.database import (
    db, User, SignupSource, DailyAppStatus, WatchlistFolder, WatchlistItem,
    WatchlistAlert, Stock, TickerMaster
)
from utils.db_queries.user_data import is_user_active
from utils.datetime_utils import get_current_utc

"""
- Move aggregates to SQL instead of Python, once user count grows
"""

def get_admin_dashboard_data():
    now = get_current_utc()

    users = get_users_before_ts(now)

    users_data = []

    for user in users:
        users_data.append({
            "account": user,
            "active": is_user_active(user)
        })

    total_users = len(users)
    start = now - timedelta(days=1)
    user_stats = get_users_stats(start, now)

    num_admins = db.session.execute(
        db.select(count(User.id))
        .where(User.is_admin == True)
    ).scalar()

    def perc(x):
        return round((x / total_users) * 100, 2) if total_users else 0

    user_stats.update({
        "active_perc": perc(user_stats["active_users"]),
        "google_perc": perc(user_stats["google_users"]),
        "email_perc": perc(user_stats["email_users"]),
        "verified_perc": perc(user_stats["verified_users"]),
        "password_perc": perc(user_stats["password_users"]),
        "google_id_perc": perc(user_stats["google_id_users"]),
        "password_and_google_id_perc": perc(user_stats["password_and_google_id_users"]),
        "email_alerts_perc": perc(user_stats["email_alerts_users"]),
        "logged_in_users_24h_perc": perc(user_stats["logged_in_users_24h"]),
        "new_users_24h_perc": perc(user_stats["new_users_24h"]),
        "num_admins": num_admins,
    })

    watchlist_stats = get_watchlist_stats(now)

    # Daily App Status for the past year
    daily_status = db.session.execute(
        db.select(DailyAppStatus)
        .order_by(DailyAppStatus.date.desc())
        .limit(365)
    ).scalars().all()

    return users_data, user_stats, watchlist_stats, daily_status

def get_users_stats(start: datetime, end: datetime):
    users = get_users_before_ts(end)

    total_users = len(users)

    active_users = 0
    google_users = 0
    email_users = 0
    verified_users = 0
    password_users = 0
    google_id_users = 0
    password_and_google_id_users = 0
    email_alerts_users = 0

    logged_in_users_24h = 0
    new_users_24h = 0

    for user in users:
        active = is_user_active(user)

        if active:
            active_users += 1

        if user.signup_source == SignupSource.GOOGLE:
            google_users += 1
        elif user.signup_source == SignupSource.EMAIL:
            email_users += 1

        if user.is_verified:
            verified_users += 1

        if user.password_hash:
            password_users += 1

        if user.google_id:
            google_id_users += 1

        if user.password_hash and user.google_id:
            password_and_google_id_users += 1

        if user.email_alerts_on:
            email_alerts_users += 1

        if user.last_login_at and user.last_login_at >= start:
            logged_in_users_24h += 1

        if start <= user.created_at < end:
            new_users_24h += 1

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "google_users": google_users,
        "email_users": email_users,
        "verified_users": verified_users,
        "password_users": password_users,
        "google_id_users": google_id_users,
        "password_and_google_id_users": password_and_google_id_users,
        "email_alerts_users": email_alerts_users,
        "logged_in_users_24h": logged_in_users_24h,
        "new_users_24h": new_users_24h,
    }

    return stats

def get_watchlist_stats(end: datetime):
    num_watchlist_folders = db.session.execute(
        db.select(func.count())
        .select_from(WatchlistFolder)
        .where(WatchlistFolder.created_at < end)
    ).scalar()

    num_watchlist_items = db.session.execute(
        db.select(func.count())
        .select_from(WatchlistItem)
        .where(WatchlistItem.created_at < end)
    ).scalar()

    num_watchlist_alerts = db.session.execute(
        db.select(func.count())
        .select_from(WatchlistAlert)
        .where(WatchlistAlert.created_at < end)
    ).scalar()

    num_ticker_watchlist_items = len(
        db.session.query(
            WatchlistItem.ticker_id
        )
        .join(TickerMaster)
        .filter(
            TickerMaster.is_active == True,
            WatchlistItem.created_at < end
        )
        .group_by(WatchlistItem.ticker_id)
        .all()
    )

    num_ticker_master = db.session.execute(
        db.select(func.count())
        .select_from(TickerMaster)
        .where(
            TickerMaster.created_at < end,
            TickerMaster.is_active == True
        )
    ).scalar()

    num_stock = db.session.execute(
        db.select(func.count())
        .select_from(Stock)
        .where(Stock.created_at < end)
    ).scalar()


    stats = {
        "num_watchlist_folders": num_watchlist_folders,
        "num_watchlist_items": num_watchlist_items,
        "num_watchlist_alerts": num_watchlist_alerts,
        "num_ticker_watchlist_items": num_ticker_watchlist_items,
        "num_ticker_master": num_ticker_master,
        "num_stock": num_stock,
    }

    return stats

def get_users_before_ts(before_ts: datetime):
    """
    ts - TimeStamp
    """
    users = db.session.execute(
        db.select(User)
        .where(User.created_at < before_ts)
    ).scalars().all()

    return users