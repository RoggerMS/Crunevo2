from crunevo.app import create_app
from typing import Tuple

app = create_app()


@app.route("/health")
def health() -> Tuple[str, int]:
    return "ok", 200
