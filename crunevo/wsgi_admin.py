import os
from crunevo import create_app

os.environ.setdefault("ADMIN_INSTANCE", "1")

app = create_app()
