from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask import request
from datetime import datetime
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Product, ProductLog, Purchase, FavoriteProduct
from crunevo.utils.credits import spend_credit
from crunevo.constants import CreditReasons

store_bp = Blueprint("store", __name__, url_prefix="/store")


def get_cart():
    return session.setdefault("cart", {})


@store_bp.route("/")
@activated_required
def store_index():
    categoria = request.args.get("categoria")
    precio_max = request.args.get("precio_max", type=float)

    query = Product.query
    if categoria:
        query = query.filter_by(category=categoria)
    if precio_max is not None:
        query = query.filter(Product.price <= precio_max)

    products = query.all()
    favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
    favorite_ids = [fav.product_id for fav in favorites]
    return render_template(
        "store/store.html",
        products=products,
        favorite_ids=favorite_ids,
        categoria=categoria,
        precio_max=precio_max,
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
    db.session.add(ProductLog(product_id=product.id, action="view"))
    db.session.commit()
    return render_template(
        "store/view_product.html", product=product, is_favorite=is_favorite
    )


@store_bp.route("/add/<int:product_id>")
@activated_required
def add_to_cart(product_id):
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    db.session.add(ProductLog(product_id=product_id, action="cart"))
    db.session.commit()
    flash("Producto agregado al carrito")
    return redirect(url_for("store.store_index"))


@store_bp.route("/redeem/<int:product_id>", methods=["POST"])
@activated_required
def redeem_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.price_credits is None:
        flash("Este producto no está disponible para canje", "warning")
        return redirect(url_for("store.view_product", product_id=product.id))
    try:
        spend_credit(
            current_user,
            product.price_credits,
            CreditReasons.COMPRA,
            related_id=product.id,
        )
    except ValueError:
        flash("Créditos insuficientes", "danger")
        return redirect(url_for("store.view_product", product_id=product.id))
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        quantity=1,
        price_credits=product.price_credits,
    )
    db.session.add(purchase)
    db.session.add(ProductLog(product_id=product.id, action="redeem"))
    db.session.commit()
    flash("Producto canjeado")
    return redirect(url_for("store.store_index"))


@store_bp.route("/buy/<int:product_id>", methods=["POST"])
@activated_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock < 1:
        flash(f"Stock insuficiente para {product.name}", "danger")
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
    return redirect(url_for("store.view_purchases"))


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


@store_bp.route("/checkout")
@activated_required
def checkout():
    cart = get_cart()
    if not cart:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for("store.view_cart"))

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = Product.query.get(pid)
        if not product or product.stock < qty:
            flash(f"Stock insuficiente para {product.name}", "danger")
            continue
        purchase = Purchase(
            user_id=current_user.id,
            product_id=product.id,
            quantity=qty,
            price_soles=product.price,
            timestamp=datetime.utcnow(),
        )
        db.session.add(purchase)
        product.stock -= qty

    db.session.commit()
    session.pop("cart", None)
    return render_template("store/checkout_success.html")


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
    favorites = FavoriteProduct.query.filter_by(user_id=current_user.id).all()
    product_ids = [fav.product_id for fav in favorites]
    products = (
        Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
    )
    return render_template("store/favorites.html", products=products)


@store_bp.route("/compras")
@activated_required
def view_purchases():
    compras = (
        Purchase.query.filter_by(user_id=current_user.id)
        .order_by(Purchase.timestamp.desc())
        .all()
    )
    return render_template("store/compras.html", compras=compras)
