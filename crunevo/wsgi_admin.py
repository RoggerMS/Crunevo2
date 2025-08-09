import os  # noqa: E402

os.environ["ADMIN_INSTANCE"] = "1"

from crunevo.app import create_app  # noqa: E402

# Expose the Flask app as `app` to mirror the main WSGI module
app = create_app()
