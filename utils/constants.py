PASSWORD_SPECIAL_CHARS_REGEX = r"[!@#$%^&*()_\-+=|\\{}\[\]:;\"'<>,.?/~` ]"
NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.-]+$"
USERNAME_ALLOWED_CHARS_REGEX = r"[a-z0-9._-]"
USERNAME_REGEX = r"^[a-z]" + USERNAME_ALLOWED_CHARS_REGEX + r"+$"
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 30
