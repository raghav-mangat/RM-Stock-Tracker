import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("FLASK_LIMITER_STORAGE_URI"),
    default_limits=[]
)