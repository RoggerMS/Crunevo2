from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import func

from crunevo.extensions import db
from crunevo.models import (
    Product,
    ProductLog,
    Purchase,
    FavoriteProduct,
    Review,
    Question,
)

product_bp = Blueprint("product", __name__)


def has_purchased(user_id: int, product_id: int) -> bool:
    return (
        Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
        is not None
    )


@product_bp.route("/producto/<int:product_id>")
def view_product(product_id: int):
    """Unified product view for store and marketplace."""
    product = Product.query.get_or_404(product_id)
    if product.is_official:
        is_favorite = (
            FavoriteProduct.query.filter_by(
                user_id=current_user.id, product_id=product.id
            ).first()
            is not None
            if current_user.is_authenticated
            else False
        )
        purchased = (
            has_purchased(current_user.id, product.id)
            if current_user.is_authenticated
            else False
        )
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
    # marketplace product
    has_purchased_flag = (
        has_purchased(current_user.id, product.id)
        if current_user.is_authenticated
        else False
    )
    related_products = (
        Product.query.filter(
            Product.id != product.id,
            Product.is_official.is_(False),
            Product.category == product.category,
        )
        .order_by(func.random())
        .limit(4)
        .all()
    )
    seller = product.seller
    product.views_count = (product.views_count or 0) + 1
    db.session.commit()
    return render_template(
        "marketplace/view_product.html",
        product=product,
        seller=seller,
        related_products=related_products,
        has_purchased=has_purchased_flag,
    )
