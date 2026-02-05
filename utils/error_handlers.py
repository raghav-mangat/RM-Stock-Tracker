from flask import render_template
from metrics import metrics
from metrics.registry import MetricName

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled Exception")
        metrics.increment(MetricName.UNCAUGHT_EXCEPTIONS)
        raise e  # Let Flask return its default error page

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        app.logger.warning("Route rate limit exceeded")
        return render_template("error/429.html"), 429