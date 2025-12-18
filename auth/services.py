from flask import request, url_for
from urllib.parse import urlparse, urljoin

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