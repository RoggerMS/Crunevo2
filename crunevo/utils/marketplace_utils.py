import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
from crunevo.models.marketplace import Seller, MarketplaceProductImage
from crunevo import db


def save_marketplace_image(file, folder="marketplace"):
    """
    Save an uploaded image to the marketplace folder with a unique filename

    Args:
        file: The uploaded file object
        folder: The subfolder within uploads to save the image (default: 'marketplace')

    Returns:
        str: The path to the saved image relative to the static folder
    """
    if not file:
        return None

    # Generate a unique filename
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Create the upload folder if it doesn't exist
    upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], folder)
    os.makedirs(upload_folder, exist_ok=True)

    # Save the file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    # Optimize the image
    try:
        optimize_image(file_path)
    except Exception as e:
        current_app.logger.error(f"Error optimizing image: {e}")

    # Return the relative path for storage in the database
    return os.path.join("uploads", folder, unique_filename)


def optimize_image(file_path, max_size=(1200, 1200), quality=85):
    """
    Optimize an image by resizing it and reducing quality

    Args:
        file_path: The path to the image file
        max_size: The maximum width and height (default: 1200x1200)
        quality: The JPEG quality (default: 85)
    """
    try:
        img = Image.open(file_path)

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if larger than max_size
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)

        # Save with optimized quality
        img.save(file_path, "JPEG", quality=quality, optimize=True)
    except Exception as e:
        current_app.logger.error(f"Error optimizing image: {e}")
        raise e


def is_user_seller(user_id):
    """
    Check if a user is registered as a seller

    Args:
        user_id: The user ID to check

    Returns:
        bool: True if the user is a seller, False otherwise
    """
    seller = Seller.query.filter_by(user_id=user_id).first()
    return seller is not None


def get_seller_by_user_id(user_id):
    """
    Get a seller by user ID

    Args:
        user_id: The user ID to check

    Returns:
        Seller: The seller object or None if not found
    """
    return Seller.query.filter_by(user_id=user_id).first()


def save_product_images(product_id, files):
    """
    Save multiple product images

    Args:
        product_id: The ID of the product
        files: List of file objects

    Returns:
        list: List of saved image paths
    """
    saved_images = []

    for i, file in enumerate(files):
        image_path = save_marketplace_image(file, folder="marketplace/products")
        if image_path:
            # Set the first image as the main image
            is_main = i == 0

            # Create a new product image
            product_image = MarketplaceProductImage(
                product_id=product_id, image_path=image_path, is_main=is_main
            )

            db.session.add(product_image)
            saved_images.append(image_path)

    db.session.commit()
    return saved_images


def delete_product_image(image_id):
    """
    Delete a product image

    Args:
        image_id: The ID of the image to delete

    Returns:
        bool: True if successful, False otherwise
    """
    image = MarketplaceProductImage.query.get(image_id)
    if not image:
        return False

    # Delete the file if it exists
    file_path = os.path.join(current_app.static_folder, image.image_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting image file: {e}")

    # Delete the database record
    db.session.delete(image)
    db.session.commit()

    return True


def get_unread_messages_count(user_id):
    """
    Get the count of unread messages for a user

    Args:
        user_id: The user ID

    Returns:
        int: The count of unread messages
    """
    from crunevo.models.marketplace import MarketplaceConversation, MarketplaceMessage

    # Get all conversations where the user is a participant
    conversations = MarketplaceConversation.query.filter(
        (MarketplaceConversation.user1_id == user_id)
        | (MarketplaceConversation.user2_id == user_id)
    ).all()

    # Count unread messages in these conversations
    unread_count = 0
    for conversation in conversations:
        unread_count += (
            MarketplaceMessage.query.filter_by(
                conversation_id=conversation.id, is_read=False
            )
            .filter(MarketplaceMessage.sender_id != user_id)
            .count()
        )

    return unread_count


def get_recent_sales(seller_id, limit=5):
    """
    Get recent sales for a seller

    Args:
        seller_id: The seller ID
        limit: The maximum number of sales to return

    Returns:
        list: List of recent sales
    """
    from crunevo.models.marketplace import MarketplaceProductSale, MarketplaceProduct

    # Get all products for this seller
    products = MarketplaceProduct.query.filter_by(seller_id=seller_id).all()
    product_ids = [p.id for p in products]

    if not product_ids:
        return []

    # Get recent sales for these products
    sales = (
        MarketplaceProductSale.query.filter(
            MarketplaceProductSale.product_id.in_(product_ids)
        )
        .order_by(MarketplaceProductSale.created_at.desc())
        .limit(limit)
        .all()
    )

    return sales


def get_recent_messages(user_id, limit=5):
    """
    Get recent messages for a user

    Args:
        user_id: The user ID
        limit: The maximum number of messages to return

    Returns:
        list: List of recent messages
    """
    from crunevo.models.marketplace import MarketplaceConversation, MarketplaceMessage

    # Get all conversations where the user is a participant
    conversations = MarketplaceConversation.query.filter(
        (MarketplaceConversation.user1_id == user_id)
        | (MarketplaceConversation.user2_id == user_id)
    ).all()

    conversation_ids = [c.id for c in conversations]

    if not conversation_ids:
        return []

    # Get recent messages from these conversations
    messages = (
        MarketplaceMessage.query.filter(
            MarketplaceMessage.conversation_id.in_(conversation_ids)
        )
        .order_by(MarketplaceMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    return messages
