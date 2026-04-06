from pathlib import Path
import json
import tempfile
import os
from flask import current_app


def write_to_data_file(filename: str, new_data: dict):
    data_dir = Path(current_app.config["DATA_FILES_DIR"])
    data_file = data_dir / filename

    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Atomic write
    with tempfile.NamedTemporaryFile(
        "w",
        dir=data_dir,
        delete=False
    ) as tmp:
        json.dump(new_data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())  # Ensures disk write
        temp_name = tmp.name

    os.replace(temp_name, data_file)

def read_data_file(filename: str) -> dict:
    data = dict()

    data_dir = Path(current_app.config["DATA_FILES_DIR"])
    data_file = data_dir / filename

    if data_file.exists():
        try:
            with open(data_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading data file: {e}")

    return data