from crunevo.app import create_app
from typing import Dict

app = create_app()


@app.route("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
