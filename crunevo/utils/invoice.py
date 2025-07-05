import os
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_invoice(purchase):
    """Create a PDF invoice for the given purchase and return its path."""
    folder = current_app.config.get("INVOICE_FOLDER", "static/invoices")
    os.makedirs(folder, exist_ok=True)
    filename = f"invoice_{purchase.id}.pdf"
    path = os.path.join(folder, filename)

    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica", 14)
    c.drawString(100, 750, "Factura de compra")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"Producto: {purchase.product.name}")
    if purchase.price_soles:
        precio = f"S/ {float(purchase.price_soles):.2f}"
    elif purchase.price_credits:
        precio = f"{purchase.price_credits} crolars"
    else:
        precio = "—"
    c.drawString(100, 700, f"Precio: {precio}")
    c.drawString(100, 680, f"Fecha: {purchase.timestamp.strftime('%d/%m/%Y %H:%M')}")
    c.drawString(100, 660, f"Código de transacción: {purchase.id}")
    c.showPage()
    c.save()

    return path
