import json
from pathlib import Path

def get_market_status():
    # Load market status
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "market_status.json"

    market_status = None
    if data_path.exists():
        with open(data_path) as f:
            market_info = json.load(f)
            market_status = market_info.get("market_status")

    return market_status

def write_to_status_file(filename, status_data):
    # Define file path
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    data_file = data_dir / filename

    # Ensure folder exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Get the existing data
    data = dict()
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        pass

    # Update the existing data
    data.update(status_data)

    # Save to JSON
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)

def get_db_populate_info():
    # Load db_populate info file
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "populate_db_info.json"

    db_populate_info = dict()
    if data_path.exists():
        with open(data_path) as f:
            info = json.load(f)
            db_populate_info = {
                "status": info.get("status"),
                "last_update_attempted": info.get("last_update_attempted"),
                "last_update_attempted_date": info.get("last_update_attempted_date"),
                "last_updated": info.get("last_updated"),
                "last_updated_date": info.get("last_updated_date"),
            }

    return db_populate_info
