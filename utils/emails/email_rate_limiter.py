from redis import Redis
from flask import current_app
from enum import Enum

class EmailType(Enum):
    VERIFY_EMAIL = 1
    RESET_PASSWORD = 2
    SETTINGS_RESET_PASSWORD = 3
    DELETE_ACCOUNT = 4

    @property
    def rate_limit(self):
        """
        Number of cooldown seconds after which we can send another email.
        """
        return {
            EmailType.VERIFY_EMAIL: 60,
            EmailType.RESET_PASSWORD: 60,
            EmailType.SETTINGS_RESET_PASSWORD: 60,
            EmailType.DELETE_ACCOUNT: 300,
        }[self]

class EmailRateLimiter:
    @staticmethod
    def __get_redis() -> Redis:
        return current_app.config["REDIS"]

    @staticmethod
    def __get_rate_limit_key(user_id: int, email_type: EmailType) -> str:
        return f"email:rate:{user_id}:{email_type}"

    @staticmethod
    def can_send_email(user_id: int, email_type: EmailType) -> tuple[bool, int]:
        redis = EmailRateLimiter.__get_redis()
        key = EmailRateLimiter.__get_rate_limit_key(user_id, email_type)

        ttl: int = redis.ttl(key)

        if ttl == -1:
            # Corrupted state: key exists without expiration
            # Repair by deleting it
            redis.delete(key)
            return True, 0

        if ttl > 0:
            return False, ttl

        # ttl == -2 (key doesn't exist) OR ttl == 0
        return True, 0

    @staticmethod
    def mark_email_sent(user_id: int, email_type: EmailType, cooldown_seconds: int) -> None:
        redis = EmailRateLimiter.__get_redis()
        key = EmailRateLimiter.__get_rate_limit_key(user_id, email_type)

        redis.set(
            key,
            1, # Placeholder value since we only need the key in Redis
            ex=cooldown_seconds
        )
