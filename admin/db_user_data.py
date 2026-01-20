from models.database import db, User, SignupSource
from utils.db_queries.user_data import is_user_active

def get_admin_dashboard_data():
    users = db.session.execute(db.select(User)).scalars().all()

    total_users = len(users)

    active_users = 0
    google_users = 0
    email_users = 0
    verified_users = 0
    password_users = 0
    google_id_users = 0
    email_alerts_users = 0

    users_data = []

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

        if user.email_alerts_on:
            email_alerts_users += 1

        users_data.append({
            "account": user,
            "active": active
        })

    def perc(x):
        return round((x / total_users) * 100, 2) if total_users else 0

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "active_perc": perc(active_users),

        "google_users": google_users,
        "google_perc": perc(google_users),

        "email_users": email_users,
        "email_perc": perc(email_users),

        "verified_users": verified_users,
        "verified_perc": perc(verified_users),

        "password_users": password_users,
        "password_perc": perc(password_users),

        "google_id_users": google_id_users,
        "google_id_perc": perc(google_id_users),

        "email_alerts_users": email_alerts_users,
        "email_alerts_perc": perc(email_alerts_users),
    }

    return users_data, stats
