from flask import Blueprint, render_template, request, jsonify
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import (
    User,
    Note,
    Post,
    Product,
    Message,
    Mission,
    Review,
    Course,
)
from sqlalchemy import or_, desc, func

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/")
@activated_required
def search_page():
    """Página principal del buscador"""
    query = request.args.get("q", "").strip()
    return render_template("search/index.html", query=query)


@search_bp.route("/api")
@activated_required
def search_api():
    """API de búsqueda universal avanzada"""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "all")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)

    if not query or len(query) < 2:
        return jsonify(
            {
                "results": [],
                "total": 0,
                "query": query,
                "suggestions": get_search_suggestions(),
            }
        )

    results = {}
    total_results = 0

    # Buscar en todas las categorías o en una específica
    if category == "all" or category == "notes":
        notes_results = search_notes(query, page, per_page)
        results["notes"] = notes_results["results"]
        total_results += notes_results["total"]

    if category == "all" or category == "posts":
        posts_results = search_posts(query, page, per_page)
        results["posts"] = posts_results["results"]
        total_results += posts_results["total"]

    if category == "all" or category == "users":
        users_results = search_users(query, page, per_page)
        results["users"] = users_results["results"]
        total_results += users_results["total"]

    if category == "all" or category == "products":
        products_results = search_products(query, page, per_page)
        results["products"] = products_results["results"]
        total_results += products_results["total"]

    if category == "all" or category == "courses":
        courses_results = search_courses(query, page, per_page)
        results["courses"] = courses_results["results"]
        total_results += courses_results["total"]

    if category == "all" or category == "chats":
        chats_results = search_chats(query, page, per_page)
        results["chats"] = chats_results["results"]
        total_results += chats_results["total"]

    if category == "all" or category == "missions":
        missions_results = search_missions(query, page, per_page)
        results["missions"] = missions_results["results"]
        total_results += missions_results["total"]

    # Sugerencias inteligentes
    suggestions = get_smart_suggestions(query)

    return jsonify(
        {
            "results": results,
            "total": total_results,
            "query": query,
            "suggestions": suggestions,
            "trending": get_trending_searches(),
            "page": page,
            "per_page": per_page,
        }
    )


def search_notes(query, page=1, per_page=20):
    """Búsqueda avanzada en apuntes"""
    base_query = Note.query

    # Búsqueda por contenido, título, tags
    search_filter = or_(
        Note.title.ilike(f"%{query}%"),
        Note.description.ilike(f"%{query}%"),
        Note.tags.ilike(f"%{query}%"),
        Note.summary.ilike(f"%{query}%"),
        Note.course.ilike(f"%{query}%"),
        Note.career.ilike(f"%{query}%"),
    )

    # Ordenar por relevancia (título tiene mayor peso)
    notes = (
        base_query.filter(search_filter)
        .order_by(
            func.case((Note.title.ilike(f"%{query}%"), 1), else_=2),
            desc(Note.created_at),
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for note in notes.items:
        content = note.description or note.summary or ""
        preview = content[:200] + "..." if len(content) > 200 else content

        results.append(
            {
                "id": note.id,
                "title": note.title,
                "content_preview": preview,
                "author": {
                    "id": note.author.id if note.author else None,
                    "username": note.author.username if note.author else "",
                    "avatar_url": note.author.avatar_url if note.author else "",
                },
                "tags": note.tags.split(",") if note.tags else [],
                "downloads": note.downloads or 0,
                "created_at": note.created_at.isoformat(),
                "url": f"/notes/{note.id}",
                "type": "note",
            }
        )

    return {"results": results, "total": notes.total, "pages": notes.pages}


def search_posts(query, page=1, per_page=20):
    """Búsqueda en publicaciones sociales"""
    base_query = Post.query.filter(Post.is_deleted.is_(False))

    search_filter = or_(
        Post.content.ilike(f"%{query}%"),
        Post.title.ilike(f"%{query}%") if hasattr(Post, "title") else False,
    )

    posts = (
        base_query.filter(search_filter)
        .order_by(desc(Post.created_at))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for post in posts.items:
        results.append(
            {
                "id": post.id,
                "content": (
                    post.content[:300] + "..."
                    if len(post.content) > 300
                    else post.content
                ),
                "author": {
                    "id": post.author.id,
                    "username": post.author.username,
                    "avatar_url": post.author.avatar_url,
                },
                "created_at": post.created_at.isoformat(),
                "likes_count": getattr(post, "likes_count", 0),
                "comments_count": getattr(post, "comments_count", 0),
                "url": f"/feed/post/{post.id}",
                "type": "post",
            }
        )

    return {"results": results, "total": posts.total, "pages": posts.pages}


def search_users(query, page=1, per_page=20):
    """Búsqueda de usuarios"""
    search_filter = or_(
        User.username.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")
    )

    users = (
        User.query.filter(User.activated.is_(True), search_filter)
        .order_by(
            func.case((User.username.ilike(f"{query}%"), 1), else_=2), desc(User.points)
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for user in users.items:
        results.append(
            {
                "id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "points": user.points,
                "verification_level": user.verification_level,
                "about": (
                    user.about[:100] + "..."
                    if user.about and len(user.about) > 100
                    else user.about
                ),
                "url": f"/perfil/{user.username}",
                "type": "user",
            }
        )

    return {"results": results, "total": users.total, "pages": users.pages}


def search_products(query, page=1, per_page=20):
    """Búsqueda en tienda"""
    search_filter = or_(
        Product.name.ilike(f"%{query}%"), Product.description.ilike(f"%{query}%")
    )

    products = (
        Product.query.filter(Product.active.is_(True), Product.stock > 0, search_filter)
        .order_by(
            func.case((Product.name.ilike(f"{query}%"), 1), else_=2),
            (
                desc(Product.popularity_score)
                if hasattr(Product, "popularity_score")
                else desc(Product.id)
            ),
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for product in products.items:
        # Calcular rating promedio
        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.product_id == product.id)
            .scalar()
            or 0
        )

        results.append(
            {
                "id": product.id,
                "name": product.name,
                "description": (
                    product.description[:200] + "..."
                    if len(product.description) > 200
                    else product.description
                ),
                "price": product.price,
                "stock": product.stock,
                "image_url": product.image_url,
                "avg_rating": round(float(avg_rating), 1),
                "url": f"/store/product/{product.id}",
                "type": "product",
            }
        )

    return {"results": results, "total": products.total, "pages": products.pages}


def search_courses(query, page=1, per_page=20):
    """Búsqueda en cursos"""
    search_filter = or_(
        Course.title.ilike(f"%{query}%"),
        Course.description.ilike(f"%{query}%"),
        Course.category.ilike(f"%{query}%"),
    )

    courses = (
        Course.query.filter(search_filter)
        .order_by(desc(Course.created_at))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for course in courses.items:
        results.append(
            {
                "id": course.id,
                "title": course.title,
                "category": course.category,
                "creator": course.creator.username if course.creator else "",
                "thumbnail_url": course.thumbnail_url,
                "url": f"/cursos/{course.id}",
                "type": "course",
            }
        )

    return {
        "results": results,
        "total": courses.total,
        "pages": courses.pages,
    }


def search_chats(query, page=1, per_page=20):
    """Búsqueda en mensajes de chat global"""
    messages = (
        Message.query.filter(
            Message.is_global.is_(True),
            Message.is_deleted.is_(False),
            Message.content.ilike(f"%{query}%"),
        )
        .order_by(desc(Message.timestamp))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for msg in messages.items:
        results.append(
            {
                "id": msg.id,
                "content": msg.content,
                "sender": {
                    "id": msg.sender.id,
                    "username": msg.sender.username,
                    "avatar_url": msg.sender.avatar_url,
                },
                "timestamp": msg.timestamp.isoformat(),
                "url": "/chat",
                "type": "chat_message",
            }
        )

    return {"results": results, "total": messages.total, "pages": messages.pages}


def search_missions(query, page=1, per_page=20):
    """Búsqueda en misiones"""
    missions = (
        Mission.query.filter(
            or_(
                Mission.description.ilike(f"%{query}%"),
                Mission.code.ilike(f"%{query}%"),
            )
        )
        .order_by(desc(Mission.credit_reward))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for mission in missions.items:
        results.append(
            {
                "id": mission.id,
                "code": mission.code,
                "description": mission.description,
                "goal": mission.goal,
                "credit_reward": mission.credit_reward,
                "url": "/misiones",
                "type": "mission",
            }
        )

    return {"results": results, "total": missions.total, "pages": missions.pages}


def get_search_suggestions():
    """Obtener sugerencias de búsqueda populares"""
    return [
        "Matemáticas",
        "Física",
        "Química",
        "Programación",
        "Historia",
        "Literatura",
        "Biología",
        "Inglés",
        "Economía",
        "Psicología",
    ]


def get_smart_suggestions(query):
    """Sugerencias inteligentes basadas en la consulta"""
    suggestions = []

    # Sugerencias basadas en tags populares
    if query:
        # Buscar tags similares
        similar_notes = Note.query.filter(Note.tags.ilike(f"%{query}%")).limit(5).all()

        for note in similar_notes:
            if note.tags:
                tags = [tag.strip() for tag in note.tags.split(",")]
                suggestions.extend(
                    [tag for tag in tags if query.lower() in tag.lower()]
                )

    return list(set(suggestions))[:10]


def get_trending_searches():
    """Obtener búsquedas trending (simulado)"""
    return [
        {"query": "Cálculo diferencial", "count": 145},
        {"query": "Programación Python", "count": 132},
        {"query": "Historia del Perú", "count": 98},
        {"query": "Química orgánica", "count": 87},
        {"query": "Inglés básico", "count": 76},
    ]


@search_bp.route("/suggestions")
@activated_required
def search_suggestions():
    """API para autocompletado"""
    query = request.args.get("q", "").strip()

    if not query or len(query) < 2:
        return jsonify([])

    # Combinar sugerencias de múltiples fuentes
    suggestions = []

    # Usuarios
    users = (
        User.query.filter(User.username.ilike(f"{query}%"), User.activated.is_(True))
        .limit(3)
        .all()
    )

    for user in users:
        suggestions.append(
            {
                "text": user.username,
                "type": "user",
                "icon": "bi-person",
                "url": f"/perfil/{user.username}",
            }
        )

    # Notas por título
    notes = Note.query.filter(Note.title.ilike(f"{query}%")).limit(3).all()

    for note in notes:
        suggestions.append(
            {
                "text": note.title,
                "type": "note",
                "icon": "bi-file-text",
                "url": f"/notes/{note.id}",
            }
        )

    # Tags populares
    tags_notes = Note.query.filter(Note.tags.ilike(f"%{query}%")).limit(3).all()

    for note in tags_notes:
        if note.tags:
            tags = [tag.strip() for tag in note.tags.split(",")]
            for tag in tags:
                if query.lower() in tag.lower() and tag not in [
                    s["text"] for s in suggestions
                ]:
                    suggestions.append(
                        {
                            "text": tag,
                            "type": "tag",
                            "icon": "bi-tag",
                            "url": f"/search?q={tag}",
                        }
                    )

    # Cursos
    courses = Course.query.filter(Course.title.ilike(f"{query}%")).limit(3).all()

    for course in courses:
        suggestions.append(
            {
                "text": course.title,
                "type": "course",
                "icon": "bi-play-circle",
                "url": f"/cursos/{course.id}",
            }
        )

    return jsonify(suggestions[:10])


@search_bp.route("/filters")
@activated_required
def search_filters():
    """Obtener filtros disponibles para búsqueda"""
    return jsonify(
        {
            "categories": [
                {"value": "all", "label": "Todo", "icon": "bi-search"},
                {"value": "notes", "label": "Apuntes", "icon": "bi-file-text"},
                {
                    "value": "posts",
                    "label": "Publicaciones",
                    "icon": "bi-chat-square-text",
                },
                {"value": "users", "label": "Usuarios", "icon": "bi-people"},
                {"value": "products", "label": "Tienda", "icon": "bi-shop"},
                {"value": "courses", "label": "Cursos", "icon": "bi-play-circle"},
                {"value": "chats", "label": "Chat", "icon": "bi-chat-dots"},
                {"value": "missions", "label": "Misiones", "icon": "bi-trophy"},
            ],
            "subjects": get_popular_subjects(),
            "time_filters": [
                {"value": "all", "label": "Todo el tiempo"},
                {"value": "today", "label": "Hoy"},
                {"value": "week", "label": "Esta semana"},
                {"value": "month", "label": "Este mes"},
                {"value": "year", "label": "Este año"},
            ],
        }
    )


def get_popular_subjects():
    """Obtener materias populares"""
    # Esto se puede hacer más sofisticado consultando la BD
    return [
        "Matemáticas",
        "Física",
        "Química",
        "Biología",
        "Historia",
        "Literatura",
        "Inglés",
        "Programación",
        "Economía",
        "Psicología",
        "Filosofía",
        "Geografía",
        "Arte",
        "Música",
        "Educación Física",
    ]
