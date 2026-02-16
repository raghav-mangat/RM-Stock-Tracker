from urllib.parse import urlparse, urljoin
from flask import request, url_for, get_flashed_messages, session, current_app, flash
from flask_login import current_user, logout_user


class RedirectService:
    @staticmethod
    def is_safe_redirect_url(target: str) -> bool:
        """
        Ensures the redirect target is local to this application.
        Prevents open redirect attacks.
        """
        if not target:
            return False

        host_url = urlparse(request.host_url)
        redirect_url = urlparse(urljoin(request.host_url, target))

        return (
                redirect_url.scheme in ("http", "https")
                and
                host_url.netloc == redirect_url.netloc
        )

    @staticmethod
    def get_post_login_redirect(default_endpoint="watchlist.index"):
        next_url = request.args.get("next")

        if next_url and RedirectService.is_safe_redirect_url(next_url):
            return next_url

        return url_for(default_endpoint)


class LogoutService:
    @staticmethod
    def perform_logout():
        user_id = current_user.id if current_user.is_authenticated else None

        # Get the flashed messages since clearing the session also clears
        # the flashed messages
        flashed_messages = get_flashed_messages(with_categories=True)

        logout_user()

        session.clear()

        current_app.logger.info(
            "User logged out",
            extra={"log_type": "auth", "user_id": user_id}
        )

        # Re-flash the flashed messages after clearing the session
        for category, message in flashed_messages:
            flash(message, category)
