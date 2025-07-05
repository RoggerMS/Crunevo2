import logging
import os
import subprocess
import tempfile
from datetime import datetime

import boto3
from flask import current_app

log = logging.getLogger(__name__)


def backup_database() -> None:
    """Dump the database and upload it to S3 or store locally."""
    db_url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    bucket = os.getenv("BACKUP_BUCKET")
    prefix = os.getenv("BACKUP_PREFIX", "backups")
    with tempfile.NamedTemporaryFile(suffix=".sql") as tmp:
        subprocess.run(["pg_dump", db_url, "-f", tmp.name], check=True)
        name = f"{datetime.utcnow():%Y-%m-%d_%H-%M-%S}.sql"
        if bucket:
            s3 = boto3.client("s3")
            key = f"{prefix}/{name}"
            s3.upload_file(tmp.name, bucket, key)
            log.info("Database backup uploaded to s3://%s/%s", bucket, key)
        else:
            dest_dir = os.getenv("BACKUP_DIR", "backups")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, name)
            subprocess.run(["cp", tmp.name, dest], check=True)
            log.info("Database backup stored at %s", dest)
