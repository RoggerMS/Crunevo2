from argon2 import PasswordHasher, exceptions as argon2_exceptions
from flask import current_app


def _make_hasher():
    cfg = current_app.config
    return PasswordHasher(
        time_cost=cfg.get("ARGON2_TIME_COST", 2),
        memory_cost=cfg.get("ARGON2_MEMORY_COST", 102400),
        parallelism=cfg.get("ARGON2_PARALLELISM", 8),
    )


def generate_hash(password: str) -> str:
    return _make_hasher().hash(password)


def verify_hash(stored: str, password: str) -> bool:
    try:
        return _make_hasher().verify(stored, password)
    except argon2_exceptions.VerifyMismatchError:
        return False
