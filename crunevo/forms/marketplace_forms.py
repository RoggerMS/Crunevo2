from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField,
    TextAreaField,
    FloatField,
    IntegerField,
    BooleanField,
    SelectField,
    SubmitField,
    HiddenField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from crunevo.models.product import ProductCategory, ProductSubcategory


class SellerRegistrationForm(FlaskForm):
    """Form for seller registration"""

    store_name = StringField(
        "Store Name",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=100,
                message="Store name must be between 3 and 100 characters",
            ),
        ],
    )
    description = TextAreaField(
        "Store Description",
        validators=[
            DataRequired(),
            Length(
                min=10,
                max=1000,
                message="Description must be between 10 and 1000 characters",
            ),
        ],
    )
    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Length(
                min=7,
                max=20,
                message="Phone number must be between 7 and 20 characters",
            ),
        ],
    )
    location = StringField(
        "Location",
        validators=[
            DataRequired(),
            Length(
                min=3, max=100, message="Location must be between 3 and 100 characters"
            ),
        ],
    )
    logo_image = FileField(
        "Store Logo",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "jpeg", "png"], "Images only!"),
        ],
    )
    banner_image = FileField(
        "Store Banner",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "jpeg", "png"], "Images only!"),
        ],
    )
    terms_accepted = BooleanField(
        "I accept the Terms and Conditions",
        validators=[DataRequired(message="You must accept the terms and conditions")],
    )
    submit = SubmitField("Register as Seller")


class ProductForm(FlaskForm):
    """Form for adding/editing products"""

    name = StringField(
        "Product Name",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=100,
                message="Product name must be between 3 and 100 characters",
            ),
        ],
    )
    description = TextAreaField(
        "Product Description",
        validators=[
            DataRequired(),
            Length(
                min=10,
                max=2000,
                message="Description must be between 10 and 2000 characters",
            ),
        ],
    )
    price = FloatField(
        "Price",
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Price must be greater than 0"),
        ],
    )
    stock = IntegerField(
        "Stock",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="Stock must be at least 1"),
        ],
    )
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    subcategory_id = SelectField("Subcategory", coerce=int, validators=[Optional()])
    condition = SelectField(
        "Condition",
        choices=[("new", "New"), ("used", "Used"), ("refurbished", "Refurbished")],
        validators=[DataRequired()],
    )
    shipping_cost = FloatField(
        "Shipping Cost",
        validators=[NumberRange(min=0, message="Shipping cost must be 0 or greater")],
    )
    shipping_time = StringField(
        "Shipping Time (e.g., 2-3 days)", validators=[DataRequired(), Length(max=50)]
    )
    free_shipping = BooleanField("Free Shipping")
    warranty = StringField("Warranty", validators=[Optional(), Length(max=100)])
    tags = StringField(
        "Tags (comma separated)", validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Save Product")

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [
            (c.id, c.name) for c in ProductCategory.query.order_by("name").all()
        ]
        self.subcategory_id.choices = [(0, "Select a subcategory")] + [
            (s.id, s.name) for s in ProductSubcategory.query.order_by("name").all()
        ]


class MessageForm(FlaskForm):
    """Form for sending messages"""

    content = TextAreaField(
        "Message",
        validators=[
            DataRequired(),
            Length(
                min=1, max=1000, message="Message must be between 1 and 1000 characters"
            ),
        ],
    )
    product_id = HiddenField("Product ID")
    seller_id = HiddenField("Seller ID")
    submit = SubmitField("Send Message")


class ProductFilterForm(FlaskForm):
    """Form for filtering products"""

    search = StringField("Search", validators=[Optional()])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    subcategory_id = SelectField("Subcategory", coerce=int, validators=[Optional()])
    min_price = FloatField("Min Price", validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField("Max Price", validators=[Optional(), NumberRange(min=0)])
    condition = SelectField(
        "Condition",
        choices=[
            ("", "All"),
            ("new", "New"),
            ("used", "Used"),
            ("refurbished", "Refurbished"),
        ],
        validators=[Optional()],
    )
    free_shipping = BooleanField("Free Shipping", validators=[Optional()])
    verified_seller = BooleanField("Verified Seller Only", validators=[Optional()])
    sort = SelectField(
        "Sort By",
        choices=[
            ("newest", "Newest"),
            ("price_asc", "Price: Low to High"),
            ("price_desc", "Price: High to Low"),
            ("popular", "Most Popular"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Apply Filters")

    def __init__(self, *args, **kwargs):
        super(ProductFilterForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(0, "All Categories")] + [
            (c.id, c.name) for c in ProductCategory.query.order_by("name").all()
        ]
        self.subcategory_id.choices = [(0, "All Subcategories")] + [
            (s.id, s.name) for s in ProductSubcategory.query.order_by("name").all()
        ]
