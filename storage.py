import json
import os

STORAGE_FILE = "records.json"


def _load() -> list:
    if not os.path.exists(STORAGE_FILE):
        return []
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: list):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_record(record: dict):
    data = _load()
    data.append(record)
    _save(data)


def get_all_records() -> list:
    return _load()


def clear_records():
    _save([])
