from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models.product import Product
from crunevo.models.purchase import Purchase
from crunevo.models.seller import Seller
from crunevo.models.marketplace_message import (
    MarketplaceMessage,
    MarketplaceConversation,
)
from crunevo.utils.uploads import save_image
from datetime import datetime

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


@marketplace_bp.route("/")
@activated_required
def marketplace_index():
    """Página principal del marketplace."""
    categoria = request.args.get("categoria")
    subcategoria = request.args.get("subcategoria")
    precio_min = request.args.get("precio_min", type=float)
    precio_max = request.args.get("precio_max", type=float)
    condicion = request.args.get("condicion")
    envio_gratis = request.args.get("envio_gratis", type=int)
    vendedor_verificado = request.args.get("vendedor_verificado", type=int)
    search = request.args.get("search")

    query = Product.query.filter(Product.seller_id.isnot(None))

    # Aplicar filtros
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

    # Ordenar productos
    sort = request.args.get("sort", "newest")
    if sort == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc())
    elif sort == "popular":
        query = query.order_by(Product.views_count.desc())

    products = query.all()

    # Obtener categorías y subcategorías para filtros
    categories = (
        db.session.query(Product.category, db.func.count(Product.id))
        .filter(Product.seller_id.isnot(None))
        .group_by(Product.category)
        .all()
    )

    subcategories = {}
    if categoria:
        subcategories = (
            db.session.query(Product.subcategory, db.func.count(Product.id))
            .filter(Product.category == categoria, Product.seller_id.isnot(None))
            .group_by(Product.subcategory)
            .all()
        )

    return render_template(
        "marketplace/index.html",
        products=products,
        categories=categories,
        subcategories=subcategories,
        filters={
            "categoria": categoria,
            "subcategoria": subcategoria,
            "precio_min": precio_min,
            "precio_max": precio_max,
            "condicion": condicion,
            "envio_gratis": envio_gratis,
            "vendedor_verificado": vendedor_verificado,
            "search": search,
            "sort": sort,
        },
    )


@marketplace_bp.route("/product/<int:product_id>")
@activated_required
def view_product(product_id):
    """Ver detalle de un producto del marketplace."""
    product = Product.query.get_or_404(product_id)

    # Incrementar contador de vistas
    product.views_count += 1
    db.session.commit()

    # Obtener información del vendedor
    seller = Seller.query.get(product.seller_id) if product.seller_id else None

    # Obtener productos relacionados
    related_products = (
        Product.query.filter(
            Product.category == product.category, Product.id != product.id
        )
        .limit(4)
        .all()
    )

    # Verificar si el usuario ha comprado el producto
    has_purchased = False
    if current_user.is_authenticated:
        has_purchased = (
            Purchase.query.filter_by(
                user_id=current_user.id, product_id=product_id
            ).first()
            is not None
        )

    return render_template(
        "marketplace/view_product.html",
        product=product,
        seller=seller,
        related_products=related_products,
        has_purchased=has_purchased,
    )


@marketplace_bp.route("/become-seller", methods=["GET", "POST"])
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
        address = request.form.get("address")

        # Validar datos
        if not store_name or not description or not contact_email:
            flash("Por favor completa todos los campos obligatorios", "danger")
            return redirect(url_for("marketplace.become_seller"))

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

    return render_template("marketplace/become_seller.html")


@marketplace_bp.route("/seller/dashboard")
@login_required
@activated_required
def seller_dashboard():
    """Panel de control para vendedores."""
    # Verificar si es vendedor
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash("Debes registrarte como vendedor primero", "warning")
        return redirect(url_for("marketplace.become_seller"))

    # Obtener productos del vendedor
    products = Product.query.filter_by(seller_id=seller.id).all()

    # Obtener estadísticas de ventas
    sales = Purchase.query.join(Product).filter(Product.seller_id == seller.id).all()

    # Obtener mensajes no leídos
    unread_messages = MarketplaceMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()

    return render_template(
        "marketplace/seller_dashboard.html",
        seller=seller,
        products=products,
        sales=sales,
        unread_messages=unread_messages,
    )


@marketplace_bp.route("/seller/products")
@login_required
@activated_required
def seller_products():
    """Gestionar productos del vendedor."""
    # Verificar si es vendedor
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash("Debes registrarte como vendedor primero", "warning")
        return redirect(url_for("marketplace.become_seller"))

    # Obtener productos del vendedor
    products = Product.query.filter_by(seller_id=seller.id).all()

    return render_template(
        "marketplace/seller_products.html",
        seller=seller,
        products=products,
    )


@marketplace_bp.route("/seller/product/add", methods=["GET", "POST"])
@login_required
@activated_required
def add_product():
    """Añadir un nuevo producto al marketplace."""
    # Verificar si es vendedor
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash("Debes registrarte como vendedor primero", "warning")
        return redirect(url_for("marketplace.become_seller"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        category = request.form.get("category")
        subcategory = request.form.get("subcategory")
        stock = request.form.get("stock")
        condition = request.form.get("condition")
        shipping_cost = request.form.get("shipping_cost")
        shipping_time = request.form.get("shipping_time")
        warranty = request.form.get("warranty")
        tags = request.form.getlist("tags")

        # Validar datos
        if not name or not description or not price or not category or not stock:
            flash("Por favor completa todos los campos obligatorios", "danger")
            return redirect(url_for("marketplace.add_product"))

        # Procesar imágenes
        image_urls = []
        if "images" in request.files:
            images = request.files.getlist("images")
            for image in images:
                if image.filename:
                    image_url = save_image(image, "marketplace/products")
                    image_urls.append(image_url)

        # Crear producto
        new_product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            subcategory=subcategory,
            stock=stock,
            condition=condition,
            shipping_cost=shipping_cost,
            shipping_time=shipping_time,
            warranty=warranty,
            tags=tags,
            seller_id=seller.id,
            image_urls=image_urls,
            is_new=True,  # Marcar como nuevo
            is_approved=False,  # Requiere aprobación
            created_at=datetime.utcnow(),
        )

        db.session.add(new_product)
        db.session.commit()

        flash(
            "Producto añadido correctamente. Será revisado antes de publicarse.",
            "success",
        )
        return redirect(url_for("marketplace.seller_products"))

    # Obtener categorías para el formulario
    from crunevo.constants import STORE_CATEGORIES

    return render_template(
        "marketplace/add_product.html",
        seller=seller,
        categories=STORE_CATEGORIES,
    )


@marketplace_bp.route("/seller/product/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@activated_required
def edit_product(product_id):
    """Editar un producto existente."""
    # Verificar si es vendedor
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash("Debes registrarte como vendedor primero", "warning")
        return redirect(url_for("marketplace.become_seller"))

    # Obtener producto
    product = Product.query.get_or_404(product_id)

    # Verificar que el producto pertenece al vendedor
    if product.seller_id != seller.id:
        flash("No tienes permiso para editar este producto", "danger")
        return redirect(url_for("marketplace.seller_products"))

    if request.method == "POST":
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.price = request.form.get("price")
        product.category = request.form.get("category")
        product.subcategory = request.form.get("subcategory")
        product.stock = request.form.get("stock")
        product.condition = request.form.get("condition")
        product.shipping_cost = request.form.get("shipping_cost")
        product.shipping_time = request.form.get("shipping_time")
        product.warranty = request.form.get("warranty")
        product.tags = request.form.getlist("tags")
        product.updated_at = datetime.utcnow()

        # Procesar imágenes nuevas
        if "images" in request.files:
            images = request.files.getlist("images")
            for image in images:
                if image.filename:
                    image_url = save_image(image, "marketplace/products")
                    if product.image_urls:
                        product.image_urls.append(image_url)
                    else:
                        product.image_urls = [image_url]

        # Eliminar imágenes seleccionadas
        images_to_remove = request.form.getlist("remove_images")
        if images_to_remove and product.image_urls:
            product.image_urls = [
                img for img in product.image_urls if img not in images_to_remove
            ]

        db.session.commit()

        flash("Producto actualizado correctamente", "success")
        return redirect(url_for("marketplace.seller_products"))

    # Obtener categorías para el formulario
    from crunevo.constants import STORE_CATEGORIES

    return render_template(
        "marketplace/edit_product.html",
        seller=seller,
        product=product,
        categories=STORE_CATEGORIES,
    )


@marketplace_bp.route("/seller/product/delete/<int:product_id>", methods=["POST"])
@login_required
@activated_required
def delete_product(product_id):
    """Eliminar un producto."""
    # Verificar si es vendedor
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash("Debes registrarte como vendedor primero", "warning")
        return redirect(url_for("marketplace.become_seller"))

    # Obtener producto
    product = Product.query.get_or_404(product_id)

    # Verificar que el producto pertenece al vendedor
    if product.seller_id != seller.id:
        flash("No tienes permiso para eliminar este producto", "danger")
        return redirect(url_for("marketplace.seller_products"))

    db.session.delete(product)
    db.session.commit()

    flash("Producto eliminado correctamente", "success")
    return redirect(url_for("marketplace.seller_products"))


@marketplace_bp.route("/messages")
@login_required
@activated_required
def messages():
    """Ver mensajes del marketplace."""
    # Obtener conversaciones del usuario
    conversations = (
        MarketplaceConversation.query.filter(
            db.or_(
                MarketplaceConversation.user1_id == current_user.id,
                MarketplaceConversation.user2_id == current_user.id,
            )
        )
        .order_by(MarketplaceConversation.last_message_at.desc())
        .all()
    )

    return render_template(
        "marketplace/messages.html",
        conversations=conversations,
    )


@marketplace_bp.route("/messages/<int:conversation_id>")
@login_required
@activated_required
def view_conversation(conversation_id):
    """Ver una conversación específica."""
    # Obtener conversación
    conversation = MarketplaceConversation.query.get_or_404(conversation_id)

    # Verificar que el usuario es parte de la conversación
    if (
        conversation.user1_id != current_user.id
        and conversation.user2_id != current_user.id
    ):
        flash("No tienes permiso para ver esta conversación", "danger")
        return redirect(url_for("marketplace.messages"))

    # Obtener mensajes
    messages = (
        MarketplaceMessage.query.filter_by(conversation_id=conversation.id)
        .order_by(MarketplaceMessage.created_at)
        .all()
    )

    # Marcar mensajes como leídos
    for message in messages:
        if message.receiver_id == current_user.id and not message.is_read:
            message.is_read = True

    db.session.commit()

    # Determinar el otro usuario
    other_user_id = (
        conversation.user2_id
        if conversation.user1_id == current_user.id
        else conversation.user1_id
    )
    from crunevo.models.user import User

    other_user = User.query.get(other_user_id)

    return render_template(
        "marketplace/view_conversation.html",
        conversation=conversation,
        messages=messages,
        other_user=other_user,
    )


@marketplace_bp.route("/messages/send", methods=["POST"])
@login_required
@activated_required
def send_message():
    """Enviar un mensaje."""
    receiver_id = request.form.get("receiver_id", type=int)
    product_id = request.form.get("product_id", type=int)
    content = request.form.get("content")
    conversation_id = request.form.get("conversation_id", type=int)

    if not content:
        flash("El mensaje no puede estar vacío", "danger")
        if conversation_id:
            return redirect(
                url_for(
                    "marketplace.view_conversation", conversation_id=conversation_id
                )
            )
        return redirect(url_for("marketplace.messages"))

    # Si hay una conversación existente
    if conversation_id:
        conversation = MarketplaceConversation.query.get_or_404(conversation_id)

        # Verificar que el usuario es parte de la conversación
        if (
            conversation.user1_id != current_user.id
            and conversation.user2_id != current_user.id
        ):
            flash(
                "No tienes permiso para enviar mensajes en esta conversación", "danger"
            )
            return redirect(url_for("marketplace.messages"))

        # Determinar el receptor
        receiver_id = (
            conversation.user2_id
            if conversation.user1_id == current_user.id
            else conversation.user1_id
        )

        # Crear mensaje
        message = MarketplaceMessage(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            product_id=conversation.product_id,
            content=content,
        )

        # Actualizar fecha de último mensaje
        conversation.last_message_at = datetime.utcnow()

        db.session.add(message)
        db.session.commit()

        return redirect(
            url_for("marketplace.view_conversation", conversation_id=conversation_id)
        )

    # Si es un nuevo mensaje
    if not receiver_id:
        flash("Destinatario no válido", "danger")
        return redirect(url_for("marketplace.messages"))

    # Verificar si ya existe una conversación entre estos usuarios para este producto
    conversation = MarketplaceConversation.query.filter(
        db.or_(
            db.and_(
                MarketplaceConversation.user1_id == current_user.id,
                MarketplaceConversation.user2_id == receiver_id,
                MarketplaceConversation.product_id == product_id,
            ),
            db.and_(
                MarketplaceConversation.user1_id == receiver_id,
                MarketplaceConversation.user2_id == current_user.id,
                MarketplaceConversation.product_id == product_id,
            ),
        )
    ).first()

    # Si no existe, crear una nueva conversación
    if not conversation:
        conversation = MarketplaceConversation(
            user1_id=current_user.id,
            user2_id=receiver_id,
            product_id=product_id,
            last_message_at=datetime.utcnow(),
        )
        db.session.add(conversation)
        db.session.flush()  # Para obtener el ID

    # Crear mensaje
    message = MarketplaceMessage(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        product_id=product_id,
        content=content,
    )

    # Actualizar fecha de último mensaje
    conversation.last_message_at = datetime.utcnow()

    db.session.add(message)
    db.session.commit()

    # Si viene de la página de producto, redirigir a la conversación
    if product_id:
        flash("Mensaje enviado correctamente", "success")
        return redirect(
            url_for("marketplace.view_conversation", conversation_id=conversation.id)
        )

    return redirect(url_for("marketplace.messages"))


@marketplace_bp.route("/seller/<int:seller_id>")
@activated_required
def view_seller(seller_id):
    """Ver perfil de un vendedor."""
    seller = Seller.query.get_or_404(seller_id)

    # Obtener productos del vendedor
    products = Product.query.filter_by(seller_id=seller_id, is_approved=True).all()

    return render_template(
        "marketplace/seller.html",
        seller=seller,
        products=products,
    )
