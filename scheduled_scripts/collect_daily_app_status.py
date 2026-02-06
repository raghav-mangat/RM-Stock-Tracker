from datetime import datetime, timedelta, UTC
from app import app
from models.database import db
from models.database import DailyAppStatus
from metrics.readers import read_daily_metrics
from admin.db_user_data import get_users_stats
from utils.datetime_utils import get_current_utc_date, format_date

"""
- Script to collect the daily app status data to be stored in the database
- First initialize the target date to be one day before the current UTC date
- Collect the metric data from Redis and user data from the database using 
    the target date
- Collect the other required data
- Store everything in the database as a single row for the target date
"""

def collect_daily_app_status():
    with app.app_context():
        redis = app.config["REDIS"]
        target_date = get_current_utc_date() - timedelta(days=1)

        # ---- Idempotency guard ----
        exists = db.session.execute(
            db.select(DailyAppStatus)
            .where(DailyAppStatus.date == target_date)
        ).scalar_one_or_none()

        if exists:
            app.logger.info(f"Daily app status already collected for {format_date(target_date)}")
            return

        # ---- Redis metrics ----
        redis_metrics = dict()
        try:
            redis_metrics = read_daily_metrics(redis, target_date)
        except Exception:
            app.logger.exception("Failed to read Redis metrics")

        # ---- Time window ----
        start_ts = datetime.combine(
            target_date, datetime.min.time(), tzinfo=UTC
        )
        end_ts = start_ts + timedelta(days=1)

        # ---- Users stats ----
        stats = get_users_stats(start_ts, end_ts)

        # ---- Deleted users (inferred) ----
        previous = db.session.execute(
            db.select(DailyAppStatus)
            .where(DailyAppStatus.date < target_date)
            .order_by(DailyAppStatus.date.desc())
            .limit(1)
        ).scalar_one_or_none()

        if previous:
            deleted_users_24h = max(
                previous.total_users + stats["new_users_24h"] - stats["total_users"],
                0
            )
        else:
            deleted_users_24h = 0

        # ---- Market status ----
        from pathlib import Path
        import json
        data_path = Path(__file__).resolve().parent.parent / "data" / "market_status.json"
        market_open = False
        if data_path.exists():
            with open(data_path) as f:
                market_info = json.load(f)
                market_status = market_info.get("market_status")
            if market_status != "closed":
                market_open = True

        # ---- Persist snapshot ----
        row = DailyAppStatus(
            date=target_date,
            deleted_users_24h=deleted_users_24h,
            market_open=market_open,
            **stats,
            **redis_metrics,
        )

        db.session.add(row)
        db.session.commit()


if __name__ == "__main__":
    collect_daily_app_status()