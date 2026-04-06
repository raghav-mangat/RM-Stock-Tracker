import os

class BaseConfig:
    ENV = os.getenv("FLASK_APP_ENV", "prod")
    RATELIMIT_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE_URI")
    FLASK_LIMITER_HASH_SECRET = os.getenv("FLASK_LIMITER_HASH_SECRET")

    # For Privacy and Terms pages
    LEGAL_LAST_UPDATED_AT = "January 1, 2026"

    DEBUG = False
    LOG_LEVEL = "INFO"
    STATUS_FILES_DIR = None
    DATA_FILES_DIR = None

class DevConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProdConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"
    STATUS_FILES_DIR = os.path.expanduser("~/status_files")
    DATA_FILES_DIR = os.path.expanduser("~/data_files")