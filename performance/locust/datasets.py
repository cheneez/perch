import json
import os
from pathlib import Path
from typing import Any


DEFAULT_PASSWORD = "testpass123"
DEFAULT_DATASET_PATH = "performance/locust/data/credentials.json"


def _default_dataset() -> dict[str, Any]:
    return {
        "students": [
            {"username": "student_seed_1", "email": "maya@bc.edu", "password": DEFAULT_PASSWORD},
            {"username": "student_seed_2", "email": "jackson@bc.edu", "password": DEFAULT_PASSWORD},
            {"username": "student_seed_3", "email": "sofia@bc.edu", "password": DEFAULT_PASSWORD},
            {"username": "student_seed_4", "email": "declan@bc.edu", "password": DEFAULT_PASSWORD},
            {"username": "student_seed_5", "email": "nina@bc.edu", "password": DEFAULT_PASSWORD},
        ],
        "lessors": [
            {"username": "lessor_seed_1", "email": "casey.agent@example.com", "password": DEFAULT_PASSWORD},
            {"username": "lessor_seed_2", "email": "riley.realty@example.com", "password": DEFAULT_PASSWORD},
            {"username": "lessor_seed_3", "email": "jordan.homes@example.com", "password": DEFAULT_PASSWORD},
            {"username": "realtor_seed", "email": "realtor@perch.dev", "password": "perch1234"},
            {"username": "testlessor1", "email": "testlessor1@realty.com", "password": DEFAULT_PASSWORD},
        ],
    }


def load_dataset() -> dict[str, Any]:
    dataset_path = os.getenv("PERCH_LOCUST_DATASET", DEFAULT_DATASET_PATH)
    file_path = Path(dataset_path)
    if not file_path.exists():
        return _default_dataset()

    try:
        loaded = json.loads(file_path.read_text())
    except json.JSONDecodeError:
        return _default_dataset()

    students = loaded.get("students", [])
    lessors = loaded.get("lessors", [])
    if not students or not lessors:
        return _default_dataset()

    return loaded

