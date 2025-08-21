from flask import Blueprint, jsonify, request
from datetime import datetime
from uuid import uuid4

personal_space_api_bp = Blueprint(
    "personal_space_api", __name__, url_prefix="/api/personal-space"
)

# In-memory store for development/testing
STORE = {"blocks": []}


def _normalize_payload(payload: dict) -> dict:
    """Normalize incoming block payload from the front-end."""
    now = datetime.utcnow().isoformat()

    # Base fields
    block_type = payload.get("type") or payload.get("wizard", {}).get("selectedType")
    title = payload.get("title", "")
    content = payload.get("description") or payload.get("content", "")

    # Defaults
    size = payload.get("size", "medium")
    color = payload.get("color", "primary")
    is_public = payload.get("public", False)

    # Start with provided metadata then overlay normalized fields
    metadata = dict(payload.get("metadata") or {})
    metadata.update(
        {
            k: v
            for k, v in payload.items()
            if k
            not in {
                "type",
                "title",
                "description",
                "content",
                "color",
                "size",
                "public",
                "metadata",
            }
        }
    )
    metadata.setdefault("size", size)
    metadata.setdefault("theme_color", color)
    metadata.setdefault("public_view", is_public)

    block = {
        "id": str(uuid4()),
        "type": block_type,
        "title": title,
        "content": content,
        "metadata": metadata,
        "created_at": now,
        "updated_at": now,
    }
    return block


@personal_space_api_bp.route("/blocks", methods=["GET"])
def list_blocks():
    """Return all blocks in the in-memory store."""
    return jsonify({"blocks": STORE["blocks"]})


@personal_space_api_bp.route("/blocks", methods=["POST"])
def create_block():
    """Create a new block, normalizing the payload before storing."""
    # Read CSRF header if present (compatibility with front-end)
    request.headers.get("X-CSRFToken")

    payload = request.get_json(silent=True) or {}
    block = _normalize_payload(payload)
    STORE["blocks"].append(block)
    return jsonify(block), 201
