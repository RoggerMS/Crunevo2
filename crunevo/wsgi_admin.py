from crunevo.app import create_app
import os

os.environ["ADMIN_INSTANCE"] = "1"

app = create_app()
