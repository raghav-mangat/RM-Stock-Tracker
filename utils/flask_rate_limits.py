from flask import request
from flask_limiter.util import get_remote_address

def ip_only():
    return get_remote_address()

def ip_and_email():
    email = request.form.get("email", "").lower().strip()
    return f"{get_remote_address()}:{email}"

def ip_and_username():
    username = request.form.get("username", "").lower().strip()
    return f"{get_remote_address()}:{username}"