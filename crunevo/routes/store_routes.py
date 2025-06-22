from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Product, ProductLog, Purchase
from crunevo.utils.credits import spend_credit
from crunevo.constants import CreditReasons

store_bp = Blueprint("store", __name__, url_prefix="/store")


def get_cart():
    return session.setdefault("cart", {})


@store_bp.route("/")
@activated_required
def store_index():
    products = Product.query.all()
    return render_template("store/store.html", products=products)


@store_bp.route("/product/<int:product_id>")
@activated_required
def view_product(product_id):
    """Show detailed information for a single product."""
    product = Product.query.get_or_404(product_id)
    db.session.add(ProductLog(product_id=product.id, action="view"))
    db.session.commit()
    return render_template("store/view_product.html", product=product)


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
    products = []
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        products.append((product, qty))
        total += float(product.price) * qty
    return render_template("store/carrito.html", products=products, total=total)


@store_bp.route("/checkout")
@activated_required
def checkout():
    session.pop("cart", None)
    flash("Compra realizada (simulada)")
    return redirect(url_for("store.store_index"))
