PASSWORD_SPECIAL_CHARS_REGEX = r"[!@#$%^&*()_\-+=|\\{}\[\]:;\"'<>,.?/~` ]"
NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.-]+$"
USERNAME_ALLOWED_CHARS_REGEX = r"[a-z0-9._-]"
USERNAME_REGEX = r"^[a-z]" + USERNAME_ALLOWED_CHARS_REGEX + r"+$"
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 30

# Number of days after which the user is considered inactive
USER_INACTIVE_DAYS_LIMIT = 90

# Number of seconds after which we can send the user a subsequent email
USER_EMAIL_COOLDOWN_SECONDS = 60