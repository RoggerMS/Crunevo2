from crunevo.app import create_app
from flask import Response

app = create_app()


@app.route("/health")
def health() -> Response:
    return Response("ok", status=200)
