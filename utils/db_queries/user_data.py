from time import time
from datetime import datetime, timedelta, UTC
from models.database import db, User
from utils.datetime_utils import convert_to_utc_tz_aware
from utils.constants import USER_INACTIVE_DAYS_LIMIT

def add_new_user(signup_source, email, username, first_name="", last_name="", password=None, google_id=None, is_verified=False):
    new_user = User(
        email=email,
        username=username,
        google_id=google_id,
        first_name=first_name,
        last_name=last_name,
        is_verified=is_verified,
        signup_source=signup_source
    )
    if password:
        new_user.password = password

    db.session.add(new_user)
    db.session.commit()
    return new_user

def add_user_google_id(user, google_id):
    user.google_id = google_id
    update_security_timestamp(user)
    db.session.commit()

def remove_user_google_id(user):
    user.google_id = None
    update_security_timestamp(user)
    db.session.commit()

def remove_user_password(user):
    user.remove_password()
    update_security_timestamp(user)
    db.session.commit()

def verify_user(user):
    user.is_verified = True
    update_security_timestamp(user)
    db.session.commit()

def change_user_password(user, password):
    user.password = password
    update_security_timestamp(user)
    db.session.commit()

def update_user_profile(user, first_name, last_name, username):
    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    db.session.commit()

def update_user_last_login_at(user):
    user.last_login_at = datetime.now(UTC)
    db.session.commit()

def toggle_user_email_alerts_on(user):
    user.email_alerts_on = not user.email_alerts_on
    db.session.commit()

def delete_user_account(user):
    db.session.delete(user)
    db.session.commit()

def update_security_timestamp(user):
    user.security_timestamp = int(time())

def get_user_by_id(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()

def get_user_by_username(username):
    return db.session.execute(db.select(User).where(User.username == username)).scalar()

def get_user_by_email(email):
    return db.session.execute(db.select(User).where(User.email == email)).scalar()

def get_user_by_google_id(google_id):
    return db.session.execute(db.select(User).where(User.google_id == google_id)).scalar()

def get_all_users():
    return db.session.execute(db.select(User)).scalars().all()

def is_user_active(user):
    user_last_login = convert_to_utc_tz_aware(user.last_login_at)

    # Time beyond which we consider the user as being inactive
    cutoff = datetime.now(UTC) - timedelta(days=USER_INACTIVE_DAYS_LIMIT)

    return user_last_login >= cutoff

def is_user_email_alert_on(user):
    return user.email_alerts_on

def user_has_watchlist_alerts(user):
    # Check if the user has any watchlist alerts
    return bool(user.watchlist_alerts)
