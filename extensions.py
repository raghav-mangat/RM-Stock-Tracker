from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Ratelimit Storage URI initialized in config
# Flask Limiter automatically looks for it in the Flask app config
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)