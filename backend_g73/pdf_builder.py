import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def build_pdf(model, color, interior, options):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"angebot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # === FONTS ===
    c.setFont("Helvetica", 10)

    # === HEADER ===
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30 * mm, height - 25 * mm, "BMW ANGEBOT")

    c.setLineWidth(1)
    c.line(30 * mm, height - 28 * mm, width - 30 * mm, height - 28 * mm)

    # === META INFO ===
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, height - 38 * mm, f"Datum: {datetime.now().strftime('%d.%m.%Y')}")

    # === BASISDATEN ===
    y = height - 55 * mm
    line_gap = 8 * mm

    def draw_row(label, value, price):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30 * mm, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(70 * mm, y, value)
        c.drawRightString(width - 30 * mm, y, f"{price} €")
        y -= line_gap

    draw_row("Modell", model["description"], model["price"])
    draw_row("Farbe", color["description"], color["price"])
    draw_row("Interieur", interior["description"], interior["price"])

    # === OPTIONEN ===
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "Optionen")
    y -= line_gap

    total = model["price"] + color["price"] + interior["price"]

    c.setFont("Helvetica", 10)
    for opt in options:
        c.drawString(32 * mm, y, f"{opt['code']} – {opt['description']}")
        c.drawRightString(width - 30 * mm, y, f"{opt['price']} €")
        total += opt["price"]
        y -= line_gap

    # === TOTAL ===
    y -= 10
    c.setLineWidth(0.5)
    c.line(30 * mm, y, width - 30 * mm, y)
    y -= line_gap

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Gesamtpreis")
    c.drawRightString(width - 30 * mm, y, f"{total} €")

    c.showPage()
    c.save()

    return filepath
