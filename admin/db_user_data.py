from datetime import datetime, timedelta
from models.database import db, User, SignupSource
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
    stats = get_users_stats(start, now)

    def perc(x):
        return round((x / total_users) * 100, 2) if total_users else 0

    stats.update({
        "active_perc": perc(stats["active_users"]),
        "google_perc": perc(stats["google_users"]),
        "email_perc": perc(stats["email_users"]),
        "verified_perc": perc(stats["verified_users"]),
        "password_perc": perc(stats["password_users"]),
        "google_id_perc": perc(stats["google_id_users"]),
        "password_and_google_id_perc": perc(stats["password_and_google_id_users"]),
        "email_alerts_perc": perc(stats["email_alerts_users"]),
        "logged_in_users_24h_perc": perc(stats["logged_in_users_24h"]),
        "new_users_24h_perc": perc(stats["new_users_24h"]),
    })

    return users_data, stats

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

def get_users_before_ts(before_ts: datetime):
    users = db.session.execute(
        db.select(User)
        .where(User.created_at < before_ts)
    ).scalars().all()

    return users