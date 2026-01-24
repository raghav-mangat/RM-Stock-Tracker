from sqlalchemy.exc import IntegrityError
from time import time
from datetime import timedelta
from models.database import db, User
from utils.datetime_utils import get_current_utc
from utils.constants import USER_INACTIVE_DAYS_LIMIT

class AuthError(Exception):
    """Base class for auth-related errors."""

def add_new_user(signup_source, email, username, first_name="", last_name="", password=None, google_id=None, is_verified=False):
    try:
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
    except IntegrityError as e:
        db.session.rollback()
        msg = str(e.orig).lower()

        if "email" in msg:
            raise AuthError("An account with this email already exists.")
        elif "username" in msg:
            raise AuthError("This username is already taken.")
        elif "google_id" in msg:
            raise AuthError("This Google account is already linked.")
        else:
            raise AuthError("Unable to create account at this time.")
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to create account at this time.")

def add_user_google_id(user, google_id):
    try:
        user.google_id = google_id
        update_security_timestamp(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AuthError(
            "This Google account is already linked to another user."
        )
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to link Google account.")

def remove_user_google_id(user):
    try:
        user.google_id = None
        update_security_timestamp(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to unlink Google account.")

def remove_user_password(user):
    try:
        user.remove_password()
        update_security_timestamp(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to remove password.")

def verify_user(user):
    try:
        user.is_verified = True
        update_security_timestamp(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to verify email.")

def change_user_password(user, password):
    try:
        user.password = password
        update_security_timestamp(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to update password.")

def update_user_profile(user, first_name, last_name, username):
    try:
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AuthError("This username is already taken.")
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to update profile.")

def toggle_user_email_alerts_on(user):
    try:
        user.email_alerts_on = not user.email_alerts_on
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to toggle email alerts.")

def update_user_last_login_at(user):
    user.last_login_at = get_current_utc()
    db.session.commit()

def delete_user_account(user):
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise AuthError("Unable to delete account.")

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
    # Time beyond which we consider the user as being inactive
    cutoff = get_current_utc() - timedelta(days=USER_INACTIVE_DAYS_LIMIT)

    return user.last_login_at >= cutoff

def is_user_email_alert_on(user):
    return user.email_alerts_on

def user_has_watchlist_alerts(user):
    # Check if the user has any watchlist alerts
    return bool(user.watchlist_alerts)
