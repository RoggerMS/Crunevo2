import os  # noqa: E402

os.environ["ADMIN_INSTANCE"] = "1"

from crunevo import create_app  # noqa: E402

app = create_app()
