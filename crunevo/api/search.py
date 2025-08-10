from flask import Blueprint, jsonify, request

search_api_bp = Blueprint("search_api", __name__, url_prefix="/api/search")


@search_api_bp.get("/suggest")
def suggest():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"query": q, "results": []})
    # TODO: Reemplazar con consultas reales (posts/notas/productos)
    # Ejemplo mínimo seguro para integrar rápido:
    results = []
    # posts = Post.query.filter(Post.title.ilike(f"%{q}%")).limit(3).all()
    # for p in posts:
    #     results.append({"type": "post", "title": p.title, "url": url_for("posts.detail", id=p.id)})
    # notes = Note.query.filter(Note.title.ilike(f"%{q}%")).limit(3).all()
    # for n in notes:
    #     results.append({"type": "note", "title": n.title, "url": url_for("notes.detail", id=n.id)})
    return jsonify({"query": q, "results": results})
