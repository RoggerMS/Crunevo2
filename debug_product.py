from crunevo.app import create_app
from crunevo.models import Product, Review, Question, Seller
from crunevo.extensions import db

app = create_app()
with app.app_context():
    try:
        print("Testing view_product function...")
        product = Product.query.filter_by(id=1).first_or_404()
        print(f"Product found: {product.name}")

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
        print(f"Related products: {len(related_products)}")

        # Get reviews
        reviews = (
            Review.query.filter_by(product_id=product.id)
            .order_by(Review.created_at.desc())
            .all()
        )
        print(f"Reviews: {len(reviews)}")

        # Get questions
        questions = (
            Question.query.filter_by(product_id=product.id)
            .order_by(Question.created_at.desc())
            .all()
        )
        print(f"Questions: {len(questions)}")

        # Get seller info if it's a marketplace product
        seller = None
        if product.seller_id:
            seller = Seller.query.get(product.seller_id)
        print(f"Seller: {seller}")

        print("All data retrieved successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
