from __future__ import annotations

import uuid
from pathlib import Path

from flask import current_app


def save_image(file, folder: str = "uploads") -> str | None:
    """Save an uploaded file inside the static directory.

    The file is stored under ``static/<folder>`` and a unique name is generated
    to avoid collisions. The returned value is the relative path that can be
    used with ``url_for('static', filename=...)``.
    """
    if not file:
        return None

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    static_folder = Path(current_app.static_folder)
    upload_folder = static_folder / folder
    upload_folder.mkdir(parents=True, exist_ok=True)

    file_path = upload_folder / filename
    file.save(file_path)

    return str(Path(folder) / filename)
