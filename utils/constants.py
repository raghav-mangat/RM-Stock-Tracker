# Users
PASSWORD_POLICY = {
    "min_length": 8,
    "max_length": 255,
    "require_upper": True,
    "require_lower": True,
    "require_number": True,
    "require_special": True,
    "special_chars_regex": r"[!@#$%^&*()_\-+=|\\{}\[\]:;\"'<>,.?/~` ]",
}
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 30
USERNAME_REGEX = rf"^(?!.*[._-]{{2}})[a-z][a-z0-9._-]{{{MIN_USERNAME_LEN-1},{MAX_USERNAME_LEN-1}}}$"
NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.\- ]+$"

MAX_NAME_LEN = 50

# Number of days after which the user is considered inactive
USER_INACTIVE_DAYS_LIMIT = 90

# Number of seconds after which we can send the user a subsequent email
USER_EMAIL_COOLDOWN_SECONDS = 60

# Watchlist
MAX_FOLDER_NAME_LEN = 100

# Number of suggestions we show in the stock search bar
NUM_SUGGESTIONS = 10

# Time after which the metrics data is removed from redis
REDIS_METRICS_TTL = 60 * 60 * 24 * 7  # 7 days