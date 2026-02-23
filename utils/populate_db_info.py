import json
from pathlib import Path
from utils.datetime_utils import get_dt_from_et_dt_str, format_date

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

    last_updated = db_last_updated()

    if last_updated:
        last_updated_date = format_date(get_dt_from_et_dt_str(last_updated))

    return last_updated_date