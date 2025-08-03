from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


def save_image(file, folder: str = "uploads") -> str:
    """Save an uploaded image and return its relative path.

    Args:
        file: Werkzeug file storage object to save.
        folder: Subdirectory within the static folder to store the file.

    Returns:
        The relative path where the file was stored.
    """
    if not file:
        raise ValueError("file is required")

    filename = secure_filename(file.filename or "")
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"

    upload_folder = Path(current_app.static_folder) / folder
    os.makedirs(upload_folder, exist_ok=True)

    file_path = upload_folder / unique_name
    file.save(file_path)

    return str(Path(folder) / unique_name)
