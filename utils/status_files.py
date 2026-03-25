import time
from pathlib import Path
import json
import tempfile
import os
from flask import current_app
from utils.datetime_utils import format_date, get_dt_from_et_dt_str


def write_to_status_file(filename: str, status_data: dict):
    status_dir = Path(current_app.config["STATUS_FILES_DIR"])
    status_file = status_dir / filename

    # Ensure directory exists
    status_dir.mkdir(parents=True, exist_ok=True)

    # Load existing data safely
    data = {}
    if status_file.exists():
        try:
            with open(status_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Corrupted file -> Overwrite safely
            data = {}

    # Update
    data.update(status_data)

    # Atomic write
    with tempfile.NamedTemporaryFile(
        "w",
        dir=status_dir,
        delete=False
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())  # Ensures disk write
        temp_name = tmp.name

    os.replace(temp_name, status_file)

def read_status_file(filename: str) -> dict:
    data = dict()

    status_dir = Path(current_app.config["STATUS_FILES_DIR"])
    status_file = status_dir / filename

    if status_file.exists():
        try:
            with open(status_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading status file: {e}")

    return data

# Simple in-memory cache
_market_status_cache = {
    "data": None,
    "last_read": 0.0
}

MARKET_STATUS_CACHE_TTL = 5  # Seconds

def get_market_status():
    now = time.time()

    # Use cache if fresh
    if _market_status_cache["data"] and (now - _market_status_cache["last_read"] < MARKET_STATUS_CACHE_TTL):
        data = _market_status_cache["data"]
    else:
        data = read_status_file("market_status.json")
        _market_status_cache["data"] = data
        _market_status_cache["last_read"] = now

    return data

def get_db_populate_status():
    return read_status_file("db_populate_status.json")

def db_last_updated():
    # Return the last updated timestamp of populate db
    data = get_db_populate_status()
    return data.get("last_updated", None) if data else None

def db_last_updated_date():
    # Return the last updated date of populate db
    last_updated_date = None

    last_updated = db_last_updated()

    if last_updated:
        last_updated_date = format_date(get_dt_from_et_dt_str(last_updated))

    return last_updated_date