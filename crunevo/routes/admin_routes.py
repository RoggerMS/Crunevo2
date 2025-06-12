import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import User, Product, Report
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.utils.helpers import admin_required
import cloudinary.uploader

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    return render_template('admin/dashboard.html', user_count=user_count)


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)


@admin_bp.route('/store', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_store():
    products = Product.query.all()
    return render_template('admin/manage_store.html', products=products)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = request.form['price']
        stock = request.form.get('stock', 0)
        file = request.files.get('image')
        image_url = None
        if file and file.filename:
            cloud_url = current_app.config.get('CLOUDINARY_URL')
            if cloud_url:
                res = cloudinary.uploader.upload(file)
                image_url = res['secure_url']
            else:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                image_url = filepath
        product = Product(name=name, description=description, price=price,
                          stock=stock, image=image_url)
        db.session.add(product)
        db.session.commit()
        flash('Producto agregado')
        return redirect(url_for('admin.manage_store'))
    return render_template('admin/add_edit_product.html')


@admin_bp.route('/reports')
@login_required
@admin_required
def manage_reports():
    reports = Report.query.all()
    return render_template('admin/manage_reports.html', reports=reports)


@admin_bp.route('/run-ranking')
@login_required
@admin_required
def run_ranking():
    calculate_weekly_ranking()
    flash('Ranking recalculado')
    return redirect(url_for('admin.dashboard'))
