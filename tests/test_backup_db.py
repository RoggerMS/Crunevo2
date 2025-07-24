import subprocess

import boto3

from crunevo.jobs.backup_db import backup_database


def test_backup_database_s3(monkeypatch, app, tmp_path):
    def fake_run(cmd, check=True, shell=False):
        with open(cmd[2], "w") as f:
            f.write("db")

    monkeypatch.setattr(subprocess, "run", fake_run)

    uploaded = {}

    class FakeClient:
        def upload_file(self, src, bucket, key):
            uploaded["src"] = src
            uploaded["bucket"] = bucket
            uploaded["key"] = key

    monkeypatch.setattr(boto3, "client", lambda *_: FakeClient())
    monkeypatch.setenv("BACKUP_BUCKET", "mybucket")
    monkeypatch.setenv("BACKUP_PREFIX", "pfx")
    with app.app_context():
        backup_database()
    assert uploaded["bucket"] == "mybucket"
    assert uploaded["key"].startswith("pfx/")


def test_backup_database_local(monkeypatch, app, tmp_path):
    def fake_run(cmd, check=True, shell=False):
        with open(cmd[2], "w") as f:
            f.write("db")

    monkeypatch.setattr(subprocess, "run", fake_run)
    dest = tmp_path / "backups"
    monkeypatch.delenv("BACKUP_BUCKET", raising=False)
    monkeypatch.setenv("BACKUP_DIR", str(dest))
    with app.app_context():
        backup_database()
    files = list(dest.iterdir())
    assert len(files) == 1
