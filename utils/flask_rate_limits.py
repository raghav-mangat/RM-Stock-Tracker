import hashlib
from flask import current_app, request
from flask_limiter.util import get_remote_address


def _hash_identifier(value: str) -> str:
    if not value:
        return "none"

    secret = current_app.config.get("FLASK_LIMITER_HASH_SECRET", "")
    data = f"{secret}:{value}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def ip_only():
    return get_remote_address()


def ip_and_email():
    email = request.form.get("email", "").lower().strip()
    return f"{get_remote_address()}:{_hash_identifier(email)}"


def ip_and_username():
    username = request.form.get("username", "").lower().strip()
    return f"{get_remote_address()}:{_hash_identifier(username)}"