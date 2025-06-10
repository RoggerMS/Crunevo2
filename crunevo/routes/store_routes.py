from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required
from app import db
from models import Product

store_bp = Blueprint('store', __name__, url_prefix='/store')


def get_cart():
    return session.setdefault('cart', {})


@store_bp.route('/')
@login_required
def store_index():
    products = Product.query.all()
    return render_template('store/store.html', products=products)


@store_bp.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('store/producto.html', product=product)


@store_bp.route('/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash('Producto agregado al carrito')
    return redirect(url_for('store.store_index'))


@store_bp.route('/cart')
@login_required
def view_cart():
    cart = get_cart()
    products = []
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        products.append((product, qty))
        total += float(product.price) * qty
    return render_template('store/carrito.html', products=products, total=total)


@store_bp.route('/checkout')
@login_required
def checkout():
    session.pop('cart', None)
    flash('Compra realizada (simulada)')
    return redirect(url_for('store.store_index'))
