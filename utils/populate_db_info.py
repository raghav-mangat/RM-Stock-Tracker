import json
from pathlib import Path

def db_last_updated():
    # Return the last updated timestamp of populate db
    last_updated = None
    data_path = Path(__file__).resolve().parent.parent / "data" / "populate_db_info.json"
    if data_path.exists():
        with open(data_path) as f:
            last_updated = json.load(f).get("last_updated")
    return last_updated

def db_last_updated_date():
    # Return the last updated date of populate db
    last_updated_date = None
    data_path = Path(__file__).resolve().parent.parent / "data" / "populate_db_info.json"
    if data_path.exists():
        with open(data_path) as f:
            last_updated_date = json.load(f).get("last_updated_date")
    return last_updated_date