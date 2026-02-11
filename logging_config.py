import logging
import os
from flask import request, g, has_request_context
from flask_login import current_user
from logging.handlers import RotatingFileHandler

"""
Notes:

- Method -> Level:
    - logger.debug() -> DEBUG
    - logger.info() -> INFO
    - logger.warning() -> WARNING
    - logger.error() -> ERROR
    - logger.exception() -> ERROR + Stack Trace
    - logger.critical() -> CRITICAL
- Special note about exception()
    - Automatically logs exc_info=True
    - Must be called inside except block
- We filter the events/auth/emails logs using:
    - extra={"log_type": ""}
    - We put this extra part in the related logger code in the project
"""

class ContextFilter(logging.Filter):
    """
    Attaches request-scoped context to log records safely.

    - Never breaks when context is missing
    - Keeps logs clean and readable
    - Allows explicit overrides via "extra"
    - Ready for structured logging / Sentry later
    - Later, you can safely add to context keys:
        - "username"
        - etc.
    """

    # Shows the values of only these specified attributes in this
    # particular order
    CONTEXT_KEYS = ("log_type", "action",
                    "request_id", "ip", "route", "user_id", "email",
                    "job_id", "recipients_count", "retries_left",
                    "reason")

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            # Attach request_id automatically if inside request context
            record.request_id = getattr(g, "request_id", None)

            # Automatically attach client IP
            record.ip = request.remote_addr

            # Attach request route
            record.route = request.path

            # If user_id was explicitly passed via "extra", do not override it
            # Otherwise, if the user is authenticated, auto-inject current_user.id
            if not hasattr(record, "user_id") and current_user.is_authenticated:
                record.user_id = current_user.id

        context_parts = []

        for key in self.CONTEXT_KEYS:
            value = getattr(record, key, None)
            if value not in (None, "", "-"):
                context_parts.append(f"{key}={value}")

        # Build a clean, readable context string
        record.context = f"[{', '.join(context_parts)}]" if context_parts else "[]"
        return True


class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level):
        super().__init__()
        self.max_level = max_level

    def filter(self, record):
        """
        Filters logs with severity <= the max_level stored
        in this class.

        Usage: handler.addFilter(MaxLevelFilter(logging.WARNING))
        """
        return record.levelno <= self.max_level


class AppOnlyFilter(logging.Filter):
    def filter(self, record):
        """
        Keeps the logs from the Flask app only.
        """
        return record.name.startswith("app")


class EventsLogFilter(logging.Filter):
    def filter(self, record):
        """
        Keeps the logs for all Flask App business events like:
            - Starting/Stopping Flask App
            - Scheduled Scripts
            - Metrics
            - etc.
        """
        events_logs_types = ["system", "scheduled_script", "metrics"]
        return getattr(record, "log_type", None) in events_logs_types


class AuthLogFilter(logging.Filter):
    def filter(self, record):
        """
        Keeps the logs for auth routes.
        """
        return getattr(record, "log_type", None) == "auth"


class EmailsLogFilter(logging.Filter):
    def filter(self, record):
        """
        Keeps the logs for email services and tasks.
        """
        return getattr(record, "log_type", None) == "emails"


class StripExceptionInfoFilter(logging.Filter):
    def filter(self, record):
        """
        Removes the stack trace and exception details from
        the log.
        """
        record.exc_info = None
        record.exc_text = None
        return True


def setup_logging(app):
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))

    # Set the log level for the Flask app and the existing handlers
    app.logger.setLevel(log_level)
    for handler in app.logger.handlers:
        handler.setLevel(log_level)

    # Decide log directory
    if app.config["ENV"] == "dev":
        log_dir = os.path.join(app.root_path, "logs")
    else:
        log_dir = os.path.expanduser("~/logs")

    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s %(context)s %(message)s"
    )

    context_filter = ContextFilter()

    """
    Separate concerns:
        - app.log: Operational truth, everything is logged here
        - error.log: Failures, captures errors/exceptions only
        - events.log: Business events for Flask App, captures info, warning, error
        - auth.log: Auth routes, captures info and warning
        - emails.log: Email services and tasks, captures info, warning, exception
    """

    # App log (DEBUG/INFO+)
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10_000_000,
        backupCount=5,
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)
    app_handler.addFilter(context_filter)

    # Error log (ERROR+)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=10_000_000,
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(context_filter)

    # Events log (INFO, WARNING, ERROR)
    events_handler = RotatingFileHandler(
        os.path.join(log_dir, "events.log"),
        maxBytes=10_000_000,
        backupCount=5,
    )
    events_handler.setLevel(logging.INFO)
    events_handler.setFormatter(formatter)
    events_handler.addFilter(context_filter)
    events_handler.addFilter(StripExceptionInfoFilter())
    events_handler.addFilter(AppOnlyFilter())
    events_handler.addFilter(EventsLogFilter())

    # Auth log (INFO, WARNING)
    auth_handler = RotatingFileHandler(
        os.path.join(log_dir, "auth.log"),
        maxBytes=10_000_000,
        backupCount=5,
    )
    auth_handler.setLevel(logging.INFO)
    auth_handler.setFormatter(formatter)
    auth_handler.addFilter(context_filter)
    auth_handler.addFilter(MaxLevelFilter(logging.WARNING))
    auth_handler.addFilter(AppOnlyFilter())
    auth_handler.addFilter(AuthLogFilter())

    # Emails log (INFO+)
    email_handler = RotatingFileHandler(
        os.path.join(log_dir, "email.log"),
        maxBytes=10_000_000,
        backupCount=5,
    )
    email_handler.setLevel(logging.INFO)
    email_handler.setFormatter(formatter)
    email_handler.addFilter(context_filter)
    email_handler.addFilter(AppOnlyFilter())
    email_handler.addFilter(EmailsLogFilter())

    """
    Later you can add:
        - Structured JSON logs
        - Centralized log aggregation (ELK, Loki)
        - Log-based alerting
        - Request tracing across services
        - Security/audit log retention policies
        - Sentry
    """

    # Remove and add the required handlers

    handlers_to_remove = []
    # Create a list of handlers to remove to avoid modifying the list while iterating
    for handler in app.logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handlers_to_remove.append(handler)

    # Remove the identified handlers
    for handler in handlers_to_remove:
        app.logger.removeHandler(handler)
        # Close the handler to release the file lock
        handler.close()

    # Attach ONLY to Flask app logger (once)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(app_handler)
        app.logger.addHandler(error_handler)
        app.logger.addHandler(events_handler)
        app.logger.addHandler(auth_handler)
        app.logger.addHandler(email_handler)

    """
    Use this in case you see duplicate logs.
    """
    # # Prevent duplicate propagation to root logger
    # app.logger.propagate = False
