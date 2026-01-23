from flask import render_template

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return render_template("error/429.html"), 429