import sys
from datetime import datetime, timedelta, UTC
from app import app
from sqlalchemy import text
from models.database import db
from models.database import DailyAppStatus
from metrics.readers import read_daily_metrics
from admin.db_user_data import get_users_stats
from utils.datetime_utils import get_current_utc_date, format_date, get_current_utc
from scheduled_scripts.helpers import get_market_status

"""
- Script to collect the daily app status data to be stored in the database
- First initialize the target date to be one day before the current UTC date
- Collect the metric data from Redis and User data from the database using 
    the target date
- Collect the Upstash Redis operational data
- Collect the MySQL database size data
- Collect the other required data
- Store everything in the database as a single row for the target date
"""


def collect_daily_app_status():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "collect_daily_app_status"}
    )

    with app.app_context():
        redis = app.config["REDIS"]
        target_date = get_current_utc_date() - timedelta(days=1)

        # ---- Idempotency guard ----
        exists = db.session.execute(
            db.select(DailyAppStatus)
            .where(DailyAppStatus.date == target_date)
        ).scalar_one_or_none()

        if exists:
            app.logger.info(
                f"Daily app status already collected for Date: {format_date(target_date)}",
                extra = {"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )
            return

        # ---- Redis metrics ----
        redis_metrics = dict()
        try:
            redis_metrics = read_daily_metrics(redis, target_date)
        except Exception:
            app.logger.exception(
                "Failed to read Redis metrics",
                extra = {"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )

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
        market_status = get_market_status()
        market_open = False
        if market_status != "closed":
            market_open = True

        # ---- Upstash Redis Data ----
        redis_data = {}

        try:
            info = redis.info()

            redis_data = {
                "redis_data_collected_at": get_current_utc(),
                "redis_total_commands": int(info.get("total_commands_processed", 0)),
                "redis_total_reads": int(info.get("total_reads_processed", 0)),
                "redis_total_writes": int(info.get("total_writes_processed", 0)),
                "redis_used_memory_bytes": int(info.get("used_memory", 0)),
                "redis_max_memory_bytes": int(info.get("maxmemory", 0)),
                "redis_keys_count": int(info.get("total_keys", 0)),
                "redis_expired_keys": int(info.get("expired_keys", 0)),
                "redis_evicted_keys": int(info.get("evicted_keys", 0)),
            }

        except Exception:
            app.logger.exception(
                "Failed to collect Upstash Redis data; continuing without Redis data",
                extra={"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )

        # ---- MySQL Database Data ----
        mysql_data = {}

        try:
            result = db.session.execute(
                text("""
                    SELECT
                      SUM(data_length + index_length) AS total_db_size,
                      SUM(data_length) AS data_size,
                      SUM(index_length) AS index_size,
                      COUNT(*) AS table_count
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE();
                """)
            ).mappings().one()

            mysql_data = {
                "mysql_data_collected_at": get_current_utc(),
                "mysql_total_db_size_bytes": int(result["total_db_size"] or 0),
                "mysql_data_size_bytes": int(result["data_size"] or 0),
                "mysql_index_size_bytes": int(result["index_size"] or 0),
                "mysql_table_count": int(result["table_count"] or 0),
            }

        except Exception:
            app.logger.exception(
                "Failed to collect MySQL database data; continuing without DB size data",
                extra={"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )

        # ---- Persist snapshot ----
        try:
            row = DailyAppStatus(
                date=target_date,
                deleted_users_24h=deleted_users_24h,
                market_open=market_open,
                **stats,
                **redis_metrics,
                **redis_data,
                **mysql_data,
            )

            db.session.add(row)
            db.session.commit()

            app.logger.info(
                f"Completed script",
                extra={"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )

        except Exception:
            app.logger.exception(
                f"Failed to store Daily App Status data for Date: {target_date}",
                extra={"log_type": "scheduled_script", "action": "collect_daily_app_status"}
            )
            sys.exit(1)


if __name__ == "__main__":
    collect_daily_app_status()