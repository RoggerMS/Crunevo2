# ruff: noqa: E402
import os

os.environ["ADMIN_INSTANCE"] = "1"

from crunevo.app import create_app

app = create_app()
