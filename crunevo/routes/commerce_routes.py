from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
)
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta
from flask_login import current_user, login_required

from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import (
    Product,
    Purchase,
    FavoriteProduct,
    Review,
    Question,
    Seller,
    MarketplaceMessage,
    MarketplaceConversation,
)
from crunevo.constants import STORE_CATEGORIES
from crunevo.utils.uploads import save_image

commerce_bp = Blueprint("commerce", __name__, url_prefix="/tienda")
# Legacy blueprints to preserve old /store and /marketplace paths
store_legacy_bp = Blueprint("store", __name__, url_prefix="/store")
marketplace_legacy_bp = Blueprint("marketplace_legacy", __name__, url_prefix="/marketplace")


def has_purchased(user_id: int, product_id: int) -> bool:
    """Return True if the user already bought the product."""
    return (
        Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
        is not None
    )


def get_cart():
    return session.setdefault("cart", {})


@commerce_bp.route("/")
def commerce_index():
    categoria = request.args.get("categoria")
    subcategoria = request.args.get("subcategoria")
    precio_min = request.args.get("precio_min", type=float)
    precio_max = request.args.get("precio_max", type=float)
    stock = request.args.get("stock", type=int)
    tags = request.args.getlist("tags")
    top = request.args.get("top", type=int)
    free = request.args.get("free", type=int)
    pack = request.args.get("pack", type=int)
    condicion = request.args.get("condicion")
    envio_gratis = request.args.get("envio_gratis", type=int)
    vendedor_verificado = request.args.get("vendedor_verificado", type=int)
    search = request.args.get("search")
    show_marketplace = request.args.get("marketplace", type=int, default=1)
    show_official = request.args.get("official", type=int, default=1)

    # Base query
    query = Product.query

    # Filter by product source
    if show_marketplace and show_official:
        # Show both marketplace and official products
        pass
    elif show_marketplace:
        # Show only marketplace products
        query = query.filter(Product.seller_id.isnot(None))
    elif show_official:
        # Show only official products
        query = query.filter_by(is_official=True)
    else:
        # Default to showing all if neither is selected
        pass

    # Apply common filters
    if categoria:
        query = query.filter_by(category=categoria)
    if subcategoria:
        query = query.filter_by(subcategory=subcategoria)
    if precio_min is not None:
        query = query.filter(Product.price >= precio_min)
    if precio_max is not None:
        query = query.filter(Product.price <= precio_max)
    if condicion:
        query = query.filter_by(condition=condicion)
    if envio_gratis:
        query = query.filter(Product.shipping_cost == 0)
    if vendedor_verificado:
        query = query.join(Seller).filter(Seller.is_verified.is_(True))
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    # Apply store-specific filters
    if free:
        query = query.filter((Product.price == 0) | (Product.price_credits == 0))
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

    # Get product ratings
    ratings = dict(
        db.session.query(Review.product_id, func.avg(Review.rating))
        .join(Product)
        .group_by(Review.product_id)
        .all()
    )

    # Get categories
    categories = [cat for group in STORE_CATEGORIES.values() for cat in group]
    categories_dict = STORE_CATEGORIES

    # Get user favorites and purchases
    favorites = []
    favorite_ids = []
    purchased_ids = []

    if current_user.is_authenticated:
        favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
        favorite_ids = [fav.product_id for fav in favorites]
        purchased = Purchase.query.filter_by(user_id=current_user.id).all()
        purchased_ids = [p.product_id for p in purchased]

    # Get featured products and top sellers
    featured_products = Product.query.filter_by(is_featured=True).all()
    top_sellers = (
        db.session.query(Product)
        .join(Purchase)
        .group_by(Product.id)
        .order_by(db.func.count(Purchase.id).desc())
        .limit(5)
        .all()
    )

    # Get category counts for marketplace view
    category_counts = {}
    for product in products:
        if product.category:
            category_counts[product.category] = (
                category_counts.get(product.category, 0) + 1
            )
    categories_with_count = [
        (cat, category_counts.get(cat, 0)) for cat in set(category_counts.keys())
    ]

    # For AJAX requests, return only product cards
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "tienda/_product_cards.html",
            products=products,
            favorite_ids=favorite_ids,
            purchased_ids=purchased_ids,
        )

    # Use the correct template for the tienda (commerce) section
    template = "tienda/tienda.html"

    return render_template(
        template,
        products=products,
        favorite_ids=favorite_ids,
        purchased_ids=purchased_ids,
        categories=categories,
        categories_dict=categories_dict,
        categories_with_count=categories_with_count,
        categoria=categoria,
        subcategoria=subcategoria,
        precio_min=precio_min,
        precio_max=precio_max,
        ratings=ratings,
        featured_products=featured_products,
        top_sellers=top_sellers,
        csrf_token=generate_csrf,
        show_marketplace=show_marketplace,
        show_official=show_official,
        filters={
            "categoria": categoria,
            "subcategoria": subcategoria,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "condicion": condicion,
            "envio_gratis": envio_gratis,
            "vendedor_verificado": vendedor_verificado,
            "search": search,
        },
    )


@commerce_bp.route("/producto/<int:product_id>")
def view_product(product_id):
    product = Product.query.filter_by(id=product_id).first_or_404()

    # Get related products
    related_products = []
    if product.category:
        related_products = (
            Product.query.filter(
                Product.category == product.category, Product.id != product.id
            )
            .order_by(db.func.random())
            .limit(4)
            .all()
        )

    # Get reviews
    reviews = (
        Review.query.filter_by(product_id=product.id)
        .order_by(Review.timestamp.desc())
        .all()
    )
    avg_rating = 0
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)

    # Get questions
    questions = (
        Question.query.filter_by(product_id=product.id)
        .order_by(Question.timestamp.desc())
        .all()
    )

    # Check if user has purchased this product
    has_bought = False
    is_favorite = False
    if current_user.is_authenticated:
        has_bought = has_purchased(current_user.id, product.id)
        is_favorite = (
            FavoriteProduct.query.filter_by(
                user_id=current_user.id, product_id=product.id
            ).first()
            is not None
        )

    # Get seller info if it's a marketplace product
    seller = None
    if product.seller_id:
        seller = Seller.query.get(product.seller_id)

    return render_template(
        "tienda/producto.html",
        product=product,
        related_products=related_products,
        reviews=reviews,
        avg_rating=avg_rating,
        questions=questions,
        has_bought=has_bought,
        is_favorite=is_favorite,
        seller=seller,
    )


# Legacy redirects for /store
@store_legacy_bp.route("/")
def store_redirect():
    params = request.args.to_dict()
    params.setdefault("official", 1)
    params.setdefault("marketplace", 0)
    return redirect(url_for("commerce.commerce_index", **params))


@store_legacy_bp.route("/product/<int:product_id>")
def store_product_redirect(product_id):
    return redirect(url_for("commerce.view_product", product_id=product_id))


@store_legacy_bp.route("/<path:path>")
def store_catch_all(path):
    query = request.query_string.decode()
    dest = f"/tienda/{path}"
    if query:
        dest += f"?{query}"
    return redirect(dest)


# Legacy redirects for /marketplace
@marketplace_legacy_bp.route("/")
def marketplace_redirect():
    params = request.args.to_dict()
    params.setdefault("official", 0)
    params.setdefault("marketplace", 1)
    return redirect(url_for("commerce.commerce_index", **params))


@marketplace_legacy_bp.route("/product/<int:product_id>")
def marketplace_product_redirect(product_id):
    return redirect(url_for("commerce.view_product", product_id=product_id))


@marketplace_legacy_bp.route("/<path:path>")
def marketplace_catch_all(path):
    query = request.query_string.decode()
    dest = f"/tienda/{path}"
    if query:
        dest += f"?{query}"
    return redirect(dest)


# Import remaining functions from store_routes.py and marketplace_routes.py
# and adapt them to the new unified blueprint


# Cart functionality
@commerce_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id).first_or_404()
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    flash(f"{product.name} añadido al carrito", "success")
    return redirect(url_for("commerce.view_product", product_id=product.id))


@commerce_bp.route("/cart/increase/<int:product_id>", methods=["POST"])
@activated_required
def increase_item(product_id):
    """Increase quantity of a product in the cart."""
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session["cart"] = cart
    return redirect(url_for("commerce.view_cart"))


@commerce_bp.route("/cart/decrease/<int:product_id>", methods=["POST"])
@activated_required
def decrease_item(product_id):
    """Decrease quantity of a product in the cart."""
    cart = get_cart()
    pid = str(product_id)
    if pid in cart:
        if cart[pid] > 1:
            cart[pid] -= 1
        else:
            cart.pop(pid)
    session["cart"] = cart
    return redirect(url_for("commerce.view_cart"))


@commerce_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@activated_required
def remove_item(product_id):
    """Remove a product from the cart."""
    cart = get_cart()
    pid = str(product_id)
    if pid in cart:
        cart.pop(pid)
    session["cart"] = cart
    return redirect(url_for("commerce.view_cart"))


@commerce_bp.route("/cart")
@activated_required
def view_cart():
    cart = get_cart()
    cart_items = []
    for pid, qty in cart.items():
        product = Product.query.filter_by(id=int(pid)).first()
        if product:
            cart_items.append({"product": product, "quantity": qty})
    return render_template("tienda/carrito.html", cart_items=cart_items)


@commerce_bp.route("/api/cart_count")
@activated_required
def cart_count_api():
    cart = get_cart()
    return jsonify({"count": sum(cart.values())})


@commerce_bp.route("/checkout", methods=["GET", "POST"])
@activated_required
def checkout():
    cart = get_cart()
    if not cart:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for("commerce.view_cart"))

    cart_items = []
    total_soles = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = Product.query.filter_by(id=pid).first()
        if product:
            cart_items.append({"product": product, "quantity": qty})
            total_soles += float(product.price) * qty

    if request.method == "GET":
        return render_template(
            "tienda/checkout_confirm.html",
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
    return render_template("tienda/checkout_success.html", download_url=download_url)


@commerce_bp.route("/compras")
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
    return render_template("tienda/compras.html", compras=compras, rango=rango)


# Seller functionality
@commerce_bp.route("/become-seller", methods=["GET", "POST"])
@login_required
@activated_required
def become_seller():
    """Formulario para convertirse en vendedor."""
    # Verificar si ya es vendedor
    existing_seller = Seller.query.filter_by(user_id=current_user.id).first()
    if existing_seller:
        return redirect(url_for("marketplace.seller_dashboard"))

    if request.method == "POST":
        store_name = request.form.get("store_name")
        description = request.form.get("description")
        contact_email = request.form.get("contact_email")
        contact_phone = request.form.get("contact_phone")
        address = request.form.get("location")

        # Validar datos
        if not store_name or not description or not contact_email:
            flash("Por favor completa todos los campos obligatorios", "danger")
            return redirect(url_for("commerce.become_seller"))

        # Procesar imágenes
        logo = None
        banner = None

        if "logo" in request.files and request.files["logo"].filename:
            logo = save_image(request.files["logo"], "marketplace/sellers")

        if "banner" in request.files and request.files["banner"].filename:
            banner = save_image(request.files["banner"], "marketplace/sellers")

        # Crear vendedor
        new_seller = Seller(
            user_id=current_user.id,
            store_name=store_name,
            description=description,
            logo=logo,
            banner=banner,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
        )

        db.session.add(new_seller)
        db.session.commit()

        flash(
            "¡Felicidades! Ahora eres un vendedor en el marketplace de Crunevo",
            "success",
        )
        return redirect(url_for("marketplace.seller_dashboard"))

    return render_template("tienda/become_seller.html")


# Favorite functionality
@commerce_bp.route("/favorite/add/<int:product_id>", methods=["POST"])
@login_required
def add_favorite(product_id):
    """Add a product to the user's favorites."""
    product = Product.query.filter_by(id=product_id).first_or_404()
    existing_fav = FavoriteProduct.query.filter_by(
        user_id=current_user.id, product_id=product.id
    ).first()

    if not existing_fav:
        db.session.add(FavoriteProduct(user_id=current_user.id, product_id=product.id))
        db.session.commit()
        flash("Producto agregado a favoritos", "success")

    return redirect(request.referrer or url_for("commerce.commerce_index"))


@commerce_bp.route("/favorite/remove/<int:product_id>", methods=["POST"])
@login_required
def remove_favorite(product_id):
    """Remove a product from the user's favorites."""
    product = Product.query.filter_by(id=product_id).first_or_404()
    fav = FavoriteProduct.query.filter_by(
        user_id=current_user.id, product_id=product.id
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Producto eliminado de favoritos", "success")

    return redirect(request.referrer or url_for("commerce.commerce_index"))


# API routes for dynamic content
@commerce_bp.route("/api/subcategorias")
def get_subcategorias():
    """Get subcategories for a given category."""
    categoria = request.args.get('categoria')
    if not categoria:
        return jsonify({'subcategorias': []})
    
    from crunevo.constants import STORE_CATEGORIES
    subcategorias = STORE_CATEGORIES.get(categoria, [])
    return jsonify({'subcategorias': subcategorias})

# Additional routes for unified commerce experience

@commerce_bp.route("/request-product", methods=["GET", "POST"])
@login_required
@activated_required
def request_product():
    """Redirect to store request product."""
    return redirect(url_for("store.request_product"))

@commerce_bp.route("/my-requests")
@login_required
@activated_required
def my_requests():
    """Redirect to store my requests."""
    return redirect(url_for("store.my_requests"))

# become_seller already exists above

@commerce_bp.route("/seller/dashboard")
@login_required
@activated_required
def seller_dashboard():
    """Redirect to marketplace seller dashboard."""
    return redirect(url_for("marketplace.seller_dashboard"))

@commerce_bp.route("/publish-product", methods=["GET", "POST"])
@login_required
@activated_required
def publish_product():
    """Redirect to marketplace add product."""
    return redirect(url_for("marketplace.add_product"))

@commerce_bp.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
@login_required
@activated_required
def edit_product(product_id):
    """Redirect to marketplace edit product."""
    return redirect(url_for("marketplace.edit_product", product_id=product_id))

@commerce_bp.route("/delete-product/<int:product_id>", methods=["POST"])
@login_required
@activated_required
def delete_product(product_id):
    """Redirect to marketplace delete product."""
    return redirect(url_for("marketplace.delete_product", product_id=product_id))

# view_purchases already exists above as compras

@commerce_bp.route("/favorites")
@login_required
@activated_required
def favorites():
    """Redirect to store favorites."""
    return redirect(url_for("store.favorites"))

@commerce_bp.route("/seller/<int:seller_id>")
@activated_required
def view_seller(seller_id):
    """Redirect to marketplace view seller."""
    return redirect(url_for("marketplace.view_seller", seller_id=seller_id))

@commerce_bp.route("/contact-seller/<int:product_id>")
@login_required
@activated_required
def contact_seller(product_id):
    """Redirect to marketplace messages."""
    return redirect(url_for("marketplace.messages"))

@commerce_bp.route("/add-review/<int:product_id>", methods=["POST"])
@login_required
@activated_required
def add_review(product_id):
    """Redirect to store add review."""
    return redirect(url_for("store.add_review", product_id=product_id))

@commerce_bp.route("/ask-question/<int:product_id>", methods=["POST"])
@login_required
@activated_required
def ask_question(product_id):
    """Redirect to store add question."""
    return redirect(url_for("store.add_question", product_id=product_id))

@commerce_bp.route("/answer-question/<int:question_id>", methods=["POST"])
@login_required
@activated_required
def answer_question(question_id):
    """Redirect to store answer question."""
    return redirect(url_for("store.answer", question_id=question_id))

@commerce_bp.route("/submit-review", methods=["POST"])
@login_required
@activated_required
def submit_review():
    """Handle review submission from compras page."""
    # This would need to be implemented based on the form data
    flash("Funcionalidad en desarrollo", "info")
    return redirect(url_for("commerce.compras"))
