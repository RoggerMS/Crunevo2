from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from models import User, Product, Report
from utils.helpers import admin_required

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


@admin_bp.route('/reports')
@login_required
@admin_required
def manage_reports():
    reports = Report.query.all()
    return render_template('admin/manage_reports.html', reports=reports)
