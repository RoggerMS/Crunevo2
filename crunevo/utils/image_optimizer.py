import logging
from PIL import Image
import io
import cloudinary.uploader


def optimize_url(
    url: str, width: int | None = None, height: int | None = None, crop: str = "fill"
) -> str:
    """Return an optimized Cloudinary URL using f_auto, q_auto and size."""
    if not url or "res.cloudinary.com" not in url:
        return url

    try:
        base, rest = url.split("/upload/", 1)
    except ValueError:
        return url

    parts = ["f_auto", "q_auto"]
    if width:
        parts.append(f"w_{width}")
    if height:
        parts.append(f"h_{height}")
    if crop:
        parts.append(f"c_{crop}")

    transform = ",".join(parts)
    return f"{base}/upload/{transform}/{rest}"


logger = logging.getLogger(__name__)


def optimize_image(image_file, max_width=800, quality=85):
    """Optimiza imágenes antes de subirlas"""
    try:
        img = Image.open(image_file)

        # Convertir RGBA a RGB si es necesario
        if img.mode == "RGBA":
            img = img.convert("RGB")

        # Redimensionar si es muy grande
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Guardar con compresión
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)

        return output
    except Exception as e:
        logger.exception("Error optimizing image: %s", e)
        return image_file


def upload_optimized_image(image_file, folder="uploads"):
    """Sube imagen optimizada a Cloudinary"""
    optimized = optimize_image(image_file)

    try:
        result = cloudinary.uploader.upload(
            optimized,
            folder=folder,
            transformation=[
                {"width": 800, "height": 600, "crop": "fill", "quality": "auto"},
                {"format": "auto"},
            ],
        )
        return result["secure_url"]
    except Exception as e:
        logger.exception("Error uploading to Cloudinary: %s", e)
        return None
