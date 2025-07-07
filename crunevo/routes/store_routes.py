from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    jsonify,
)
import os
from datetime import datetime, timedelta
from flask_login import current_user
from flask import current_app
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import (
    Product,
    ProductLog,
    Purchase,
    FavoriteProduct,
    Review,
    Question,
    Answer,
)
from crunevo.utils.credits import spend_credit
from crunevo.constants import CreditReasons, AchievementCodes
from crunevo.utils import unlock_achievement

store_bp = Blueprint("store", __name__, url_prefix="/store")


def has_purchased(user_id: int, product_id: int) -> bool:
    """Return True if the user already bought the product."""
    return (
        Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
        is not None
    )


def get_cart():
    return session.setdefault("cart", {})


@store_bp.route("/")
@activated_required
def store_index():
    categoria = request.args.get("categoria")
    precio_max = request.args.get("precio_max", type=float)
    stock = request.args.get("stock", type=int)
    tags = request.args.getlist("tags")
    top = request.args.get("top", type=int)
    free = request.args.get("free", type=int)
    pack = request.args.get("pack", type=int)

    query = Product.query
    if categoria:
        query = query.filter_by(category=categoria)
    if free:
        query = query.filter((Product.price == 0) | (Product.price_credits == 0))
    if precio_max is not None:
        query = query.filter(Product.price <= precio_max)
    if stock:
        query = query.filter(Product.stock > 0)
    if "Premium" in tags:
        query = query.filter(Product.credits_only.is_(True))
    if "Ofertas" in tags:
        query = query.filter(Product.is_featured.is_(True))
    if "Digital" in tags:
        query = query.filter(Product.download_url.isnot(None))
    if "Físico" in tags:
        query = query.filter(Product.download_url.is_(None))

    if top:
        from sqlalchemy import func

        query = (
            query.outerjoin(Purchase)
            .group_by(Product.id)
            .order_by(func.count(Purchase.id).desc())
            .limit(10)
        )
    elif pack:
        query = query.filter_by(category="Pack")

    products = query.all()
    from sqlalchemy import func

    ratings = dict(
        db.session.query(Review.product_id, func.avg(Review.rating))
        .group_by(Review.product_id)
        .all()
    )
    categories = [
        c[0] for c in db.session.query(Product.category).distinct().all() if c[0]
    ]
    favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
    favorite_ids = [fav.product_id for fav in favorites]
    purchased = Purchase.query.filter_by(user_id=current_user.id).all()
    purchased_ids = [p.product_id for p in purchased]
    featured_products = Product.query.filter_by(is_featured=True).all()
    from sqlalchemy import func

    top_sellers = (
        db.session.query(Product)
        .join(Purchase)
        .group_by(Product.id)
        .order_by(func.count(Purchase.id).desc())
        .limit(5)
        .all()
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "store/_product_cards.html",
            products=products,
            favorite_ids=favorite_ids,
            purchased_ids=purchased_ids,
        )

    return render_template(
        "store/store.html",
        products=products,
        favorite_ids=favorite_ids,
        purchased_ids=purchased_ids,
        categories=categories,
        categoria=categoria,
        precio_max=precio_max,
        ratings=ratings,
        featured_products=featured_products,
        top_sellers=top_sellers,
    )


@store_bp.route("/product/<int:product_id>")
@activated_required
def view_product(product_id):
    """Show detailed information for a single product."""
    product = Product.query.get_or_404(product_id)
    is_favorite = (
        FavoriteProduct.query.filter_by(
            user_id=current_user.id, product_id=product.id
        ).first()
        is not None
    )
    purchased = has_purchased(current_user.id, product.id)
    from sqlalchemy import func

    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter_by(product_id=product.id)
        .scalar()
    )
    reviews = (
        Review.query.filter_by(product_id=product.id)
        .options(db.joinedload(Review.user))
        .order_by(Review.timestamp.desc())
        .all()
    )
    questions = (
        Question.query.filter_by(product_id=product.id)
        .options(db.joinedload(Question.user))
        .order_by(Question.timestamp.desc())
        .all()
    )
    # Suggest products from the same category to show in the sidebar
    from sqlalchemy import func

    recommended_products = (
        Product.query.filter(
            Product.id != product.id, Product.category == product.category
        )
        .order_by(func.random())
        .limit(4)
        .all()
    )
    db.session.add(ProductLog(product_id=product.id, action="view"))
    db.session.commit()
    return render_template(
        "store/view_product.html",
        product=product,
        is_favorite=is_favorite,
        purchased=purchased,
        avg_rating=avg_rating or 0,
        reviews=reviews,
        questions=questions,
        recommended_products=recommended_products,
    )


@store_bp.route("/product/<int:product_id>/review", methods=["POST"])
@activated_required
def add_review(product_id: int):
    """Allow a user to leave a review for a purchased product."""
    if not has_purchased(current_user.id, product_id):
        flash("Debes adquirir el producto para reseñarlo", "warning")
        return redirect(url_for("store.view_product", product_id=product_id))
    rating = int(request.form.get("rating", 0))
    comment = request.form.get("comment", "")
    if rating < 1 or rating > 5:
        flash("Calificación inválida", "danger")
        return redirect(url_for("store.view_product", product_id=product_id))
    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()
    flash("Reseña agregada", "success")
    return redirect(url_for("store.view_product", product_id=product_id))


@store_bp.route("/product/<int:product_id>/question", methods=["POST"])
@activated_required
def add_question(product_id: int):
    body = request.form.get("body", "").strip()
    if not body:
        flash("Pregunta vacía", "warning")
        return redirect(url_for("store.view_product", product_id=product_id))
    q = Question(user_id=current_user.id, product_id=product_id, body=body)
    db.session.add(q)
    db.session.commit()
    flash("Pregunta publicada", "success")
    return redirect(url_for("store.view_product", product_id=product_id))


@store_bp.route("/answer/<int:question_id>", methods=["POST"])
@activated_required
def add_answer(question_id: int):
    body = request.form.get("body", "").strip()
    if not body:
        flash("Respuesta vacía", "warning")
        return redirect(request.referrer or url_for("store.store_index"))
    ans = Answer(question_id=question_id, user_id=current_user.id, body=body)
    db.session.add(ans)
    db.session.commit()
    unlock_achievement(current_user, AchievementCodes.TUTOR_ACTIVO)
    flash("Respuesta publicada", "success")
    q = Question.query.get_or_404(question_id)
    return redirect(url_for("store.view_product", product_id=q.product_id))


@store_bp.route("/add/<int:product_id>", methods=["GET", "POST"])
@activated_required
def add_to_cart(product_id):
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    db.session.add(ProductLog(product_id=product_id, action="cart"))
    db.session.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"count": sum(cart.values())})
    flash("Producto agregado al carrito")
    return redirect(url_for("store.store_index"))


@store_bp.route("/redeem/<int:product_id>", methods=["POST"])
@activated_required
def redeem_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.price_credits is None:
        flash("Este producto no está disponible para canje", "warning")
        return redirect(url_for("store.view_product", product_id=product.id))
    if product.stock < 1:
        flash("Producto sin stock", "danger")
        return redirect(url_for("store.view_product", product_id=product.id))
    if not product.allow_multiple and has_purchased(current_user.id, product.id):
        flash("Ya adquiriste este producto", "warning")
        return redirect(url_for("store.view_product", product_id=product.id))
    try:
        spend_credit(
            current_user,
            product.price_credits,
            CreditReasons.COMPRA,
            related_id=product.id,
        )
    except ValueError:
        flash("Crolars insuficientes", "danger")
        return redirect(url_for("store.view_product", product_id=product.id))
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        quantity=1,
        price_credits=product.price_credits,
    )
    db.session.add(purchase)
    product.stock -= 1
    db.session.add(ProductLog(product_id=product.id, action="redeem"))
    db.session.commit()
    flash("Producto canjeado", "success")
    return render_template(
        "store/checkout_success.html", download_url=product.download_url
    )


@store_bp.route("/buy/<int:product_id>", methods=["POST"])
@activated_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock < 1:
        flash(f"Stock insuficiente para {product.name}", "danger")
        return redirect(url_for("store.view_product", product_id=product.id))
    if not product.allow_multiple and has_purchased(current_user.id, product.id):
        flash("Ya adquiriste este producto", "warning")
        return redirect(url_for("store.view_product", product_id=product.id))

    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        quantity=1,
        price_soles=product.price,
        timestamp=datetime.utcnow(),
    )
    db.session.add(purchase)
    product.stock -= 1
    db.session.commit()
    flash("Producto comprado exitosamente", "success")
    return render_template(
        "store/checkout_success.html", download_url=product.download_url
    )


@store_bp.route("/cart/increase/<int:product_id>", methods=["POST"])
@activated_required
def increase_item(product_id):
    """Increase quantity of a product in the cart."""
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    return redirect(url_for("store.view_cart"))


@store_bp.route("/cart/decrease/<int:product_id>", methods=["POST"])
@activated_required
def decrease_item(product_id):
    """Decrease quantity or remove item if reaches zero."""
    cart = get_cart()
    pid = str(product_id)
    if pid in cart:
        if cart[pid] > 1:
            cart[pid] -= 1
        else:
            cart.pop(pid)
    session["cart"] = cart
    return redirect(url_for("store.view_cart"))


@store_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@activated_required
def remove_item(product_id):
    """Remove a product from the cart."""
    cart = get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("store.view_cart"))


@store_bp.route("/cart")
@activated_required
def view_cart():
    cart = get_cart()
    cart_items = []
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            cart_items.append({"product": product, "quantity": qty})
    return render_template("store/carrito.html", cart_items=cart_items)


@store_bp.route("/api/cart_count")
@activated_required
def cart_count_api():
    cart = get_cart()
    return jsonify({"count": sum(cart.values())})


@store_bp.route("/checkout", methods=["GET", "POST"])
@activated_required
def checkout():
    cart = get_cart()
    if not cart:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for("store.view_cart"))

    cart_items = []
    total_soles = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = Product.query.get(pid)
        if product:
            cart_items.append({"product": product, "quantity": qty})
            total_soles += float(product.price) * qty

    if request.method == "GET":
        return render_template(
            "store/checkout_confirm.html",
            cart_items=cart_items,
            total_soles=total_soles,
        )

    download_url = None
    shipping_option = request.form.get("shipping_option")
    shipping_address = None
    if shipping_option == "delivery":
        shipping_address = request.form.get("shipping_address")
    shipping_message = request.form.get("shipping_message")
    purchases_created = []
    for item in cart_items:
        product = item["product"]
        qty = item["quantity"]
        if product.stock < qty:
            flash(f"Stock insuficiente para {product.name}", "danger")
            continue
        if not product.allow_multiple and has_purchased(current_user.id, product.id):
            flash(f"Ya adquiriste {product.name}", "warning")
            continue
        purchase = Purchase(
            user_id=current_user.id,
            product_id=product.id,
            quantity=qty,
            price_soles=product.price,
            shipping_address=shipping_address,
            shipping_message=shipping_message,
            timestamp=datetime.utcnow(),
        )
        db.session.add(purchase)
        purchases_created.append(purchase)
        product.stock -= qty
        if qty == 1 and product.download_url and not download_url:
            download_url = product.download_url

    db.session.commit()
    from crunevo.utils.invoice import generate_invoice

    for purchase in purchases_created:
        generate_invoice(purchase)
    session.pop("cart", None)
    return render_template("store/checkout_success.html", download_url=download_url)


@store_bp.route("/favorite/<int:product_id>", methods=["POST"])
@activated_required
def toggle_favorite(product_id):
    """Add or remove a product from the user's favorites."""
    fav = FavoriteProduct.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()
    if fav:
        db.session.delete(fav)
        flash("Producto eliminado de favoritos")
    else:
        db.session.add(FavoriteProduct(user_id=current_user.id, product_id=product_id))
        flash("Producto agregado a favoritos")
    db.session.commit()
    return redirect(request.referrer or url_for("store.store_index"))


@store_bp.route("/favorites")
@activated_required
def view_favorites():
    """Display the user's favorite products."""
    categoria = request.args.get("categoria")
    tipo = request.args.get("tipo")
    favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
    product_ids = [fav.product_id for fav in favorites]
    query = (
        Product.query.filter(Product.id.in_(product_ids))
        if product_ids
        else Product.query.filter(False)
    )
    if categoria:
        query = query.filter_by(category=categoria)
    if tipo == "pack":
        query = query.filter_by(category="Pack")
    if tipo == "gratis":
        query = query.filter((Product.price == 0) | (Product.price_credits == 0))
    if tipo == "nuevo":
        query = query.filter_by(is_new=True)
    products = query.all()
    purchased = Purchase.query.filter_by(user_id=current_user.id).all()
    purchased_ids = [p.product_id for p in purchased]
    categories = [
        c[0] for c in db.session.query(Product.category).distinct().all() if c[0]
    ]
    return render_template(
        "store/favorites.html",
        products=products,
        purchased_ids=purchased_ids,
        categoria=categoria,
        tipo=tipo,
        categories=categories,
    )


@store_bp.route("/compras")
@activated_required
def view_purchases():
    rango = request.args.get("r")
    query = Purchase.query.filter_by(user_id=current_user.id)
    now = datetime.utcnow()
    if rango == "7d":
        start = now - timedelta(days=7)
        query = query.filter(Purchase.timestamp >= start)
    elif rango == "1m":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Purchase.timestamp >= start)
    elif rango == "3m":
        start = now - timedelta(days=90)
        query = query.filter(Purchase.timestamp >= start)

    compras = query.order_by(Purchase.timestamp.desc()).all()
    return render_template("store/compras.html", compras=compras, rango=rango)


@store_bp.route("/comprobante/<int:purchase_id>")
@activated_required
def download_receipt(purchase_id: int):
    purchase = Purchase.query.filter_by(
        id=purchase_id, user_id=current_user.id
    ).first_or_404()
    folder = current_app.config.get("INVOICE_FOLDER", "static/invoices")
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)
    filename = f"invoice_{purchase.id}.pdf"
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        from crunevo.utils.invoice import generate_invoice

        generate_invoice(purchase)
    return send_file(
        path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"comprobante_{purchase.id}.pdf",
    )


@store_bp.route("/api/search")
@activated_required
def search_products():
    """Return paginated product results as HTML for AJAX search."""
    query_str = request.args.get("q", "").strip()
    page = request.args.get("page", type=int, default=1)

    categoria = request.args.get("categoria")
    precio_max = request.args.get("precio_max", type=float)
    stock = request.args.get("stock", type=int)
    tags = request.args.getlist("tags")
    top = request.args.get("top", type=int)
    free = request.args.get("free", type=int)
    pack = request.args.get("pack", type=int)

    query = Product.query
    if categoria:
        query = query.filter_by(category=categoria)
    if free:
        query = query.filter((Product.price == 0) | (Product.price_credits == 0))
    if precio_max is not None:
        query = query.filter(Product.price <= precio_max)
    if stock:
        query = query.filter(Product.stock > 0)
    if "Premium" in tags:
        query = query.filter(Product.credits_only.is_(True))
    if "Ofertas" in tags:
        query = query.filter(Product.is_featured.is_(True))
    if "Digital" in tags:
        query = query.filter(Product.download_url.isnot(None))
    if "Físico" in tags:
        query = query.filter(Product.download_url.is_(None))

    if query_str:
        from sqlalchemy import or_

        search_filter = or_(
            Product.name.ilike(f"%{query_str}%"),
            Product.description.ilike(f"%{query_str}%"),
        )
        query = query.filter(search_filter)

    if top:
        from sqlalchemy import func

        query = (
            query.outerjoin(Purchase)
            .group_by(Product.id)
            .order_by(func.count(Purchase.id).desc())
        )
    elif pack:
        query = query.filter_by(category="Pack")

    products = query.paginate(page=page, per_page=20, error_out=False)

    favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
    favorite_ids = [fav.product_id for fav in favorites]
    purchased = Purchase.query.filter_by(user_id=current_user.id).all()
    purchased_ids = [p.product_id for p in purchased]

    html = render_template(
        "store/_product_cards.html",
        products=products.items,
        favorite_ids=favorite_ids,
        purchased_ids=purchased_ids,
    )

    return jsonify({"html": html, "has_next": products.has_next, "page": page})
