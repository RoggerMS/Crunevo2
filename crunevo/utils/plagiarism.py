import hashlib
import json
import os
from flask import current_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "data"))
HASH_FILE = os.path.join(BASE_DIR, "note_hashes.json")


def _load_hashes():
    try:
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_hashes(data: dict) -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def compute_hash(fileobj) -> str:
    """Return SHA-256 hex digest of a file-like object."""
    try:
        fileobj.seek(0)
    except Exception:
        current_app.logger.exception("Error seeking file object")
    hasher = hashlib.sha256()
    for chunk in iter(lambda: fileobj.read(8192), b""):
        hasher.update(chunk)
    try:
        fileobj.seek(0)
    except Exception:
        current_app.logger.exception("Error seeking file object")
    return hasher.hexdigest()


def get_duplicate(file_hash: str):
    """Return note id for existing hash or None."""
    hashes = _load_hashes()
    return hashes.get(file_hash)


def record_hash(note_id: int, file_hash: str) -> None:
    hashes = _load_hashes()
    hashes[file_hash] = note_id
    _save_hashes(hashes)
