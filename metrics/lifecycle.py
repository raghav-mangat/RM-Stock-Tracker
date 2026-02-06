import atexit
import signal
import sys
import threading


def register_metrics_shutdown(app, metrics):
    """
    Ensure metrics are flushed on process shutdown.
    Works outside Flask request/app context.
    """

    logger = app.logger

    def flush_and_exit(signum=None):
        try:
            if signum:
                reason = f"signal:{signal.Signals(signum).name}"
            else:
                reason = "atexit"

            level = logger.info if signum else logger.debug
            level("Flushing metrics on shutdown", extra={"reason": reason})
            metrics.flush()
        except Exception:
            # Never let shutdown crash the process
            logger.exception("Failed to flush metrics on shutdown")
        finally:
            # Re-raise default behavior
            if signum is not None:
                sys.exit(0)

    # Normal interpreter exit
    atexit.register(lambda: flush_and_exit())

    # Process termination signals, only in the main thread
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda s, f: flush_and_exit(s))