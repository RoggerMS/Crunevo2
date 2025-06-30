from PIL import Image
import io
import cloudinary.uploader


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
        print(f"Error optimizing image: {e}")
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
        print(f"Error uploading to Cloudinary: {e}")
        return None
