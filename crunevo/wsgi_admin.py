import os
from crunevo.app import create_app

os.environ["ADMIN_INSTANCE"] = "1"

app = create_app()
