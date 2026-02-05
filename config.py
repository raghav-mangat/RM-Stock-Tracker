import os

class BaseConfig:
    ENV = os.getenv("FLASK_APP_ENV", "prod")
    RATELIMIT_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE_URI")

    DEBUG = False
    LOG_LEVEL = "INFO"

class DevConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProdConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"