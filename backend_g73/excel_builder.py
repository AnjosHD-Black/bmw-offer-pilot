from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.pagebreak import Break
from openpyxl.drawing.image import Image
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.cell import column_index_from_string, get_column_letter, coordinate_from_string
from openpyxl.utils.units import pixels_to_EMU
from datetime import datetime
import os
import json


def underline(ws, cell):
    ws[cell].font = Font(underline="single", bold=True)


def center_cell(ws, cell):
    ws[cell].alignment = Alignment(horizontal="center")


def set_number_format(ws, cell):
    ws[cell].number_format = "0.00"


def set_currency_format(ws, cell):
    ws[cell].number_format = '0.00 "€"'


def apply_dropdown_style(ws, cell):
    ws[cell].font = Font(bold=True)


def load_country_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "country_pak_client_g73.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_image_mappings():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "image_mappings_g73.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def insert_exterior_image(ws, vehicle_data: dict, anchor="D3", size_px=None, size_in=None, image_index=0):
    """Insert exterior image based on color (farbe), tires (reifen), and authority codes"""
    print("[DEBUG] insert_exterior_image called")
    
    image_mappings = load_image_mappings()
    print(f"[DEBUG] image_mappings: {image_mappings}")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "images")
    
    # Extract farbe (exterior_color) code
    exterior_color = vehicle_data.get("exterior_color")
    print(f"[DEBUG] exterior_color: {exterior_color}")
    
    farbe_code = None
    if isinstance(exterior_color, dict):
        farbe_code = exterior_color.get("code")
    else:
        farbe_code = exterior_color
    
    if farbe_code not in image_mappings.get("farben", []):
        print(f"[DEBUG] Farbe {farbe_code} not found in mappings, returning")
        return
    
    # Extract reifen code
    standard_list = vehicle_data.get("standard", [])
    security_list = vehicle_data.get("security", [])
    all_codes = standard_list + security_list
    
    reifen_code = None
    for item in all_codes:
        code = item.get("code") if isinstance(item, dict) else item
        if code in image_mappings.get("reifen", []):
            reifen_code = code
            break
    
    if not reifen_code:
        print(f"[DEBUG] No reifen code found, using default 10X")
        reifen_code = "10X"
    
    print(f"[DEBUG] Using farbe={farbe_code}, reifen={reifen_code}")
    
    # Check for authority codes (141 or 144)
    authority_codes = image_mappings.get("authority_codes", ["141", "144"])
    has_authority = False
    
    for item in security_list:
        code = item.get("code") if isinstance(item, dict) else item
        if code in authority_codes:
            has_authority = True
            break
    
    auth_variant = "authority" if has_authority else "private"
    print(f"[DEBUG] has_authority={has_authority}, variant={auth_variant}")
    
    # Determine position (front or rear)
    position = "front" if image_index == 0 else "rear"

    style_code = None
    for item in all_codes:
        code = item.get("code") if isinstance(item, dict) else item
        if code in ["346", "7M9"]:
            style_code = str(code).upper()
            break

    # Construct filename
    if style_code:
        filename = f"{farbe_code}_{reifen_code}_{auth_variant}_{style_code}_{position}.jpg"
    else:
        filename = f"{farbe_code}_{reifen_code}_{auth_variant}_{position}.jpg"
    image_path = os.path.join(images_dir, filename)
    
    print(f"[DEBUG] Looking for: {filename}")
    print(f"[DEBUG] Full path: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"[DEBUG] Image not found: {image_path}")
        return
    
    print(f"[DEBUG] Image found, adding to worksheet")
    
    try:
        img = Image(image_path)
        print(f"[DEBUG] Image loaded, original size - Height: {img.height}, Width: {img.width}")
        
        if size_in is not None:
            target_width_px = int(round(size_in[0] * 96))
            target_height_px = int(round(size_in[1] * 96))
        elif size_px is not None:
            target_width_px, target_height_px = size_px
        else:
            # Calibrated values for exact 2.2" × 1.32" in Excel
            target_width_px = 196
            target_height_px = 118

        img.width = target_width_px
        img.height = target_height_px
        
        print(f"[DEBUG] Setting image size: {img.width}px × {img.height}px")
        
        ws.add_image(img, anchor)
        print(f"[DEBUG] Image added to {anchor}")
    except Exception as e:
        print(f"[ERROR] Error inserting image: {e}")
        import traceback
        traceback.print_exc()


def insert_interior_image(
    ws,
    vehicle_data: dict,
    anchor="A1",
    size_in=None,
    image_index=0,
    align_right_cell=None,
    right_offset_px=0,
):
    """Insert interior image based on leder (leather) and trim codes."""
    print("[DEBUG] insert_interior_image called")

    image_mappings = load_image_mappings()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "images")

    # Extract leder code (interior leather/color)
    interior_color = vehicle_data.get("interior_color")
    print(f"[DEBUG] interior_color: {interior_color}")

    leder_code = None
    if isinstance(interior_color, dict):
        leder_code = interior_color.get("code")
    else:
        leder_code = interior_color

    if leder_code not in image_mappings.get("leder", []):
        print(f"[DEBUG] Leder {leder_code} not found in mappings")
        return

    # Extract trim code (interior_trim)
    # First check dedicated interior_trim field
    interior_trim = vehicle_data.get("interior_trim")
    trim_code = None
    
    if isinstance(interior_trim, dict):
        code = interior_trim.get("code")
        if code in image_mappings.get("trim", []):
            trim_code = code
    
    # If not found, check in optional list
    if not trim_code:
        optional_list = vehicle_data.get("optional", [])
        for item in optional_list:
            code = item.get("code") if isinstance(item, dict) else item
            if code in image_mappings.get("trim", []):
                trim_code = code
                break
    
    if not trim_code:
        print(f"[DEBUG] No trim code found, using default 43E")
        trim_code = "43E"
    
    print(f"[DEBUG] Using leder={leder_code}, trim={trim_code}")
    
    # Determine position (1 or 2)
    position = str((image_index % 2) + 1)

    style_code = None
    all_codes = []
    for bucket in [vehicle_data.get("standard", []), vehicle_data.get("security", []), vehicle_data.get("optional", [])]:
        for item in bucket:
            code = item.get("code") if isinstance(item, dict) else item
            if code in ["346", "7M9"]:
                style_code = str(code).upper()
                break
        if style_code:
            break

    # Construct filename
    if style_code:
        filename = f"{leder_code}_{trim_code}_{style_code}_interior_{position}.jpg"
    else:
        filename = f"{leder_code}_{trim_code}_interior_{position}.jpg"
    image_path = os.path.join(images_dir, filename)
    
    print(f"[DEBUG] Looking for: {filename}")
    print(f"[DEBUG] Full path: {image_path}")

    if not os.path.exists(image_path):
        print(f"[DEBUG] Interior image not found: {image_path}")
        return

    try:
        img = Image(image_path)
        print(f"[DEBUG] Interior image loaded, original size - Height: {img.height}, Width: {img.width}")

        target_width_px = img.width
        target_height_px = img.height
        if size_in is not None:
            target_width_px = int(round(size_in[0] * 96))
            target_height_px = int(round(size_in[1] * 96))
            img.width = target_width_px
            img.height = target_height_px

        if align_right_cell:
            img.anchor = build_right_aligned_anchor(
                ws,
                align_right_cell,
                target_width_px,
                target_height_px,
                extra_offset_px=right_offset_px,
            )
            ws.add_image(img)
            print(f"[DEBUG] Interior image right-aligned to {align_right_cell}")
        else:
            ws.add_image(img, anchor)
            print(f"[DEBUG] Interior image added to {anchor}")
    except Exception as e:
        print(f"[ERROR] Error inserting interior image: {e}")
        import traceback
        traceback.print_exc()


def bottom_border(ws, row):
    for col in ["A", "B", "C", "D", "E", "F", "G"]:
        ws[f"{col}{row}"].border = Border(bottom=Side(style="thin"))


def double_bottom_border(ws, row):
    for col in ["A", "B", "C", "D", "E", "F", "G"]:
        ws[f"{col}{row}"].border = Border(bottom=Side(style="double"))


def apply_box_border(ws, start_row, end_row, start_col="A", end_col="G", style="thin"):
    side = Side(style=style)
    for row in range(start_row, end_row + 1):
        for col in range(ord(start_col), ord(end_col) + 1):
            cell = ws[f"{chr(col)}{row}"]
            border = cell.border
            cell.border = Border(
                left=side if col == ord(start_col) else border.left,
                right=side if col == ord(end_col) else border.right,
                top=side if row == start_row else border.top,
                bottom=side if row == end_row else border.bottom,
            )


def column_width_to_pixels(width):
    if width is None:
        width = 8.43
    return int(width * 7 + 5)


def build_right_aligned_anchor(
    ws,
    cell_ref,
    image_width_px,
    image_height_px,
    extra_offset_px=0,
):
    col_letter, row = coordinate_from_string(cell_ref)
    target_col_idx = column_index_from_string(col_letter)

    widths = {
        idx: column_width_to_pixels(ws.column_dimensions[get_column_letter(idx)].width)
        for idx in range(1, target_col_idx + 1)
    }

    remaining = image_width_px
    anchor_col_idx = target_col_idx
    while remaining > widths[anchor_col_idx] and anchor_col_idx > 1:
        remaining -= widths[anchor_col_idx]
        anchor_col_idx -= 1

    col_off_px = max(widths[anchor_col_idx] - remaining + extra_offset_px, 0)

    marker = AnchorMarker(
        col=anchor_col_idx - 1,
        row=row - 1,
        colOff=pixels_to_EMU(col_off_px),
        rowOff=0,
    )
    ext = XDRPositiveSize2D(pixels_to_EMU(image_width_px), pixels_to_EMU(image_height_px))
    return OneCellAnchor(_from=marker, ext=ext)


def build_excel(vehicle_data: dict) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Quotation"
    
    # Set default font to Calibri for the entire workbook
    default_font = Font(name="Calibri", size=11)
    
    # Apply to all cells by setting the default style
    from openpyxl.styles import NamedStyle
    calibri_style = NamedStyle(name="calibri_default", font=default_font)
    if "calibri_default" not in wb.named_styles:
        wb.add_named_style(calibri_style)

    # Load country data
    country_data = load_country_data()
    countries_list = country_data.get("countries", [])

    # =========================
    # COLUMNS
    # =========================
    ws.column_dimensions["A"].width = 17.82
    ws.column_dimensions["B"].width = 11.82
    ws.column_dimensions["C"].width = 45.73
    ws.column_dimensions["D"].width = 16.64
    ws.column_dimensions["E"].width = 21.18
    ws.column_dimensions["F"].width = 17.36
    ws.column_dimensions["G"].width = 19

    # =========================
    # PRINT HEADER (ALL PAGES)
    # =========================
    ws.oddHeader.left.text = "LOGO 1"
    ws.oddHeader.right.text = "LOGO 2"

    # =========================
    # PAGE 1
    # =========================
    ws["B1"] = "BMW 7"
    ws["B1"].font = Font(name="Calibri", size=11, bold=True)
    ws["E1"] = datetime.today().strftime("%d.%m.%Y")
    
    bottom_border(ws, 1)

    ws["A2"] = "Quotation"
    ws["B2"] = ""
    ws["E2"] = "=J3"

    ws["A3"] = "Department"
    ws["B3"] = ""
    ws["E3"] = ""

    ws["A4"] = "Type"
    ws["B4"] = "X5"

    ws["A5"] = "Country"
    ws["B5"] = "=J3"

    ws["A6"] = "Model Year"
    ws["B6"] = "=YEAR(H3)"
    ws["B6"].alignment = Alignment(horizontal="left")

    ws["A7"] = ""
    ws["B7"] = ""
    ws["B7"].alignment = Alignment(horizontal="left")
    ws["E7"] = ""
    ws["E7"].alignment = Alignment(horizontal="left")

    ws["A8"] = "Vehicle Status"
    ws["B8"] = '=IF(H3>TODAY(),"BTO","Stock")'

    bottom_border(ws, 8)

    # New columns H, I, J (right side)
    ws["H2"] = "Prod. Date"
    ws["I2"] = "KW"
    ws["J2"] = "Country"

    ws["H3"] = ""
    ws["H3"].number_format = "DD.MM.YYYY"
    ws["I3"] = f"=WEEKNUM(H3,21)"
    ws["J3"] = ""

    ws["H4"] = "PAK"
    ws["I4"] = "Client"

    ws["H5"] = f'=IFERROR(VLOOKUP(J3,Countries!$A$2:$C$4,2,0),"")'
    ws["I5"] = f'=IFERROR(VLOOKUP(J3,Countries!$A$2:$C$4,3,0),"")'

    ws["H6"] = "8R3"
    ws["H7"] = f'=IF(COUNTIF(B:B,"8R3")>0,"OK","NOT OK")'

    # Undefinierte Codes aus der Eingabe rechts in Spalte J anzeigen.
    unknown_codes = vehicle_data.get("unknown_codes", [])
    ws["J13"] = "Undefined Option Codes"
    ws["J13"].font = Font(name="Calibri", size=10, bold=True, underline="single")
    for idx, code in enumerate(unknown_codes, start=14):
        ws[f"J{idx}"] = code
    
    # Add borders to H6 and H7
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    ws["H6"].border = thin_border
    ws["H7"].border = thin_border
    
    # Add borders to H2-J2, H3-J3, H4-I4, H5-I5
    for cell_ref in ["H2", "I2", "J2", "H3", "I3", "J3", "H4", "I4", "H5", "I5"]:
        ws[cell_ref].border = thin_border
    
    # Add conditional formatting to H7: red background if 8R3 is not present
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    red_font = Font(color="FFFFFF")
    cf_rule = FormulaRule(formula=[f'=COUNTIF(B:B,"8R3")=0'], fill=red_fill, font=red_font)
    ws.conditional_formatting.add(f'H7', cf_rule)

    ws["D9"] = "=H5"
    ws["D9"].font = Font(name="Calibri", size=8, underline="single")
    ws["D9"].alignment = Alignment(horizontal="right")
    
    ws["E9"] = "Page 1"
    ws["E9"].font = Font(name="Calibri", size=6)
    ws["E9"].alignment = Alignment(horizontal="right")

    ws["B10"] = "Option Code"
    ws["C10"] = "Description"
    ws["E10"] = "Price EUR"
    ws["E10"].alignment = Alignment(horizontal="right")
    ws["F10"] = "Price WHS EUR"
    ws["F10"].alignment = Alignment(horizontal="right")
    ws["G10"] = "Price WHS GOV EUR"
    ws["G10"].alignment = Alignment(horizontal="right")

    underline(ws, "B10")
    underline(ws, "C10")
    underline(ws, "E10")
    underline(ws, "F10")
    underline(ws, "G10")

    row = 11

    # ----- BASIC VEHICLE -----
    base_row_map = {}
    base_rows = [
        ("base_vehicle", "Basic Vehicle", vehicle_data.get("base_vehicle") or {}),
        ("exterior_color", "Exterior Color", vehicle_data.get("exterior_color") or {}),
        ("interior_color", "Interior Color", vehicle_data.get("interior_color") or {}),
        ("interior_trim", "Interior Trim", vehicle_data.get("interior_trim") or {}),
    ]

    for key, label, item in base_rows:
        base_row_map[key] = row
        ws[f"A{row}"] = label
        underline(ws, f"A{row}")
        ws[f"B{row}"] = item.get("code", "")
        center_cell(ws, f"B{row}")
        ws[f"C{row}"] = item.get("text", "")
        ws[f"E{row}"] = item.get("price", 0.0)
        set_number_format(ws, f"E{row}")
        ws[f"F{row}"] = f"=E{row}*0.9"
        set_number_format(ws, f"F{row}")
        ws[f"G{row}"] = f"=F{row}*0.9"
        set_number_format(ws, f"G{row}")
        row += 1

    base_vehicle_row = base_row_map.get("base_vehicle")
    exterior_color_row = base_row_map.get("exterior_color")
    interior_color_row = base_row_map.get("interior_color")
    interior_trim_row = base_row_map.get("interior_trim")

    bottom_border(ws, row - 1)

    def write_section(start_row, label, items, fill_formulas=True):
        ws[f"A{start_row}"] = label
        underline(ws, f"A{start_row}")

        if not items:
            return start_row + 1, None, None

        first = items[0]
        ws[f"B{start_row}"] = first.get("code", "")
        center_cell(ws, f"B{start_row}")
        ws[f"C{start_row}"] = first.get("text", "")
        ws[f"E{start_row}"] = first.get("price", 0.0)
        set_number_format(ws, f"E{start_row}")
        if fill_formulas:
            ws[f"F{start_row}"] = f"=E{start_row}*0.9"
            set_number_format(ws, f"F{start_row}")
            ws[f"G{start_row}"] = f"=F{start_row}*0.9"
            set_number_format(ws, f"G{start_row}")
        start_item_row = start_row
        end_item_row = start_row

        row_cursor = start_row + 1
        for item in items[1:]:
            ws[f"B{row_cursor}"] = item.get("code", "")
            center_cell(ws, f"B{row_cursor}")
            ws[f"C{row_cursor}"] = item.get("text", "")
            ws[f"E{row_cursor}"] = item.get("price", 0.0)
            set_number_format(ws, f"E{row_cursor}")
            if fill_formulas:
                ws[f"F{row_cursor}"] = f"=E{row_cursor}*0.9"
                set_number_format(ws, f"F{row_cursor}")
                ws[f"G{row_cursor}"] = f"=F{row_cursor}*0.9"
                set_number_format(ws, f"G{row_cursor}")
            end_item_row = row_cursor
            row_cursor += 1

        return row_cursor, start_item_row, end_item_row

    # ----- STANDARD EQUIPMENT -----
    row, _, _ = write_section(row, "Standard Equipment", vehicle_data.get("standard", []))
    row += 1

    # ----- PROTECTION PACKAGE -----
    protection_row = row
    ws[f"A{row}"] = "Protection Package"
    underline(ws, f"A{row}")
    ws[f"C{row}"] = "VR Protection"
    
    # Top border für Protection Package Zeile (A:G)
    top_border_line = Border(top=Side(style='thin'))
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        ws[f"{col}{row}"].border = top_border_line
    
    row += 1

    protection_texts = [
        "External",
        "Heated",
        "Safety",
        "Underbody"
    ]

    for text in protection_texts:
        ws[f"C{row}"] = text
        row += 1

    page2_row = row
    ws[f"A{row}"] = "=A7"
    ws[f"A{row}"].alignment = Alignment(horizontal="left")
    ws[f"B{row}"] = "=B7"
    ws[f"B{row}"].alignment = Alignment(horizontal="left")
    ws[f"E{row}"] = "Page 2"
    ws[f"E{row}"].font = Font(name="Calibri", size=9)
    ws[f"E{row}"].alignment = Alignment(horizontal="right")
    
    # Bottom border für Page 2 Zeile (A:G)
    bottom_border_line = Border(bottom=Side(style='thin'))
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        if not ws[f"{col}{page2_row}"].border:
            ws[f"{col}{page2_row}"].border = bottom_border_line
        else:
            ws[f"{col}{page2_row}"].border = Border(
                bottom=Side(style='thin'),
                left=ws[f"{col}{page2_row}"].border.left,
                right=ws[f"{col}{page2_row}"].border.right,
                top=ws[f"{col}{page2_row}"].border.top
            )
    
    row += 1

    # ----- SECURITY EQUIPMENT -----
    security_items = vehicle_data.get("security", [])
    security_items_start = None
    security_items_end = None

    ws[f"A{row}"] = "Security Equipment"
    underline(ws, f"A{row}")

    if security_items:
        first_item = security_items[0]
        ws[f"B{row}"] = first_item.get("code", "")
        center_cell(ws, f"B{row}")
        ws[f"C{row}"] = first_item.get("text", "")
        ws[f"E{row}"] = first_item.get("price", 0.0)
        set_number_format(ws, f"E{row}")
        ws[f"F{row}"] = f"=E{row}*0.9"
        set_number_format(ws, f"F{row}")
        ws[f"G{row}"] = f"=F{row}*0.9"
        set_number_format(ws, f"G{row}")
        security_items_start = row
        security_items_end = row
        row += 1

        for item in security_items[1:]:
            security_items_end = row
            ws[f"B{row}"] = item.get("code", "")
            center_cell(ws, f"B{row}")
            ws[f"C{row}"] = item.get("text", "")
            ws[f"E{row}"] = item.get("price", 0.0)
            set_number_format(ws, f"E{row}")
            ws[f"F{row}"] = f"=E{row}*0.9"
            set_number_format(ws, f"F{row}")
            ws[f"G{row}"] = f"=F{row}*0.9"
            set_number_format(ws, f"G{row}")
            row += 1
    else:
        row += 1

    # Border line after security items (A:G)
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        ws[f"{col}{row}"].border = Border(bottom=Side(style='thin'))
    row += 1

    row, optional_items_start, optional_items_end = write_section(
        row,
        "Optional Equipment",
        vehicle_data.get("optional", [])
    )

    row += 1

    technical_adjustments_row = row
    technical_adjustments_header_row = row
    
    # Add top border from A to G
    for col in ["A", "B", "C", "D", "E", "F", "G"]:
        ws[f"{col}{row}"].border = Border(top=Side(style='thin'))
    
    ws[f"A{row}"] = "Technical Adjustments"
    underline(ws, f"A{row}")
    ws[f"B{row}"] = "940"
    ws[f"C{row}"] = "SPECIAL EQUIPMENT ON DEMAND"
    row += 1

    ws[f"A{row}"] = "Additions"
    underline(ws, f"A{row}")
    row += 1
    
    additions_start_row = row
    # Write additions from vehicle_data
    additions = vehicle_data.get("additions", [])
    for addition in additions:
        ws[f"B{row}"] = addition.get("code", "")
        ws[f"C{row}"] = addition.get("text", "")
        ws[f"E{row}"] = addition.get("price", 0.0)
        set_currency_format(ws, f"E{row}")
        row += 1
    
    additions_end_row = row - 1 if additions else None
    
    # Add sum formula to Technical Adjustments header row E
    if additions_end_row and additions_end_row >= additions_start_row:
        ws[f"E{technical_adjustments_header_row}"] = f"=SUM(E{additions_start_row}:E{additions_end_row})"
    else:
        ws[f"E{technical_adjustments_header_row}"] = 0.0
    set_currency_format(ws, f"E{technical_adjustments_header_row}")
    
    ws[f"F{technical_adjustments_header_row}"] = f"=E{technical_adjustments_header_row}"
    set_currency_format(ws, f"F{technical_adjustments_header_row}")
    ws[f"G{technical_adjustments_header_row}"] = f"=E{technical_adjustments_header_row}"
    set_currency_format(ws, f"G{technical_adjustments_header_row}")
    
    # Add one empty line after additions
    row += 1
    
    ws[f"A{row}"] = "Deletions"
    underline(ws, f"A{row}")

    # One empty line before pricing block
    row += 1

    # Top border above pricing block
    bottom_border(ws, row)
    row += 1

    basic_vehicle_price_row = row
    ws[f"B{row}"] = "Basic Vehicle Price"
    ws[f"E{row}"] = f"=E{base_vehicle_row}"
    ws[f"F{row}"] = f"=F{base_vehicle_row}"
    ws[f"G{row}"] = f"=G{base_vehicle_row}"
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    row += 1

    security_options_price_row = row
    ws[f"B{row}"] = "Security Options"
    if security_items_start and security_items_end:
        ws[f"E{row}"] = f"=SUM(E{security_items_start}:E{security_items_end})"
        ws[f"F{row}"] = f"=SUM(F{security_items_start}:F{security_items_end})"
        ws[f"G{row}"] = f"=SUM(G{security_items_start}:G{security_items_end})"
    else:
        ws[f"E{row}"] = 0.0
        ws[f"F{row}"] = 0.0
        ws[f"G{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    row += 1

    optional_equipment_price_row = row
    ws[f"B{row}"] = "Optional Equipment"
    optional_sum_parts_e = [
        f"E{r}"
        for r in [exterior_color_row, interior_color_row, interior_trim_row]
        if r
    ]
    optional_sum_parts_f = [
        f"F{r}"
        for r in [exterior_color_row, interior_color_row, interior_trim_row]
        if r
    ]
    optional_sum_parts_g = [
        f"G{r}"
        for r in [exterior_color_row, interior_color_row, interior_trim_row]
        if r
    ]

    if optional_items_start and optional_items_end:
        optional_sum_parts_e.append(f"E{optional_items_start}:E{optional_items_end}")
        optional_sum_parts_f.append(f"F{optional_items_start}:F{optional_items_end}")
        optional_sum_parts_g.append(f"G{optional_items_start}:G{optional_items_end}")

    if optional_sum_parts_e:
        ws[f"E{row}"] = "=SUM(" + ",".join(optional_sum_parts_e) + ")"
        ws[f"F{row}"] = "=SUM(" + ",".join(optional_sum_parts_f) + ")"
        ws[f"G{row}"] = "=SUM(" + ",".join(optional_sum_parts_g) + ")"
    else:
        ws[f"E{row}"] = 0.0
        ws[f"F{row}"] = 0.0
        ws[f"G{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    row += 1

    technical_adjustment_price_row = row
    ws[f"B{row}"] = "Technical Adjustment"
    ws[f"E{row}"] = f"=E{technical_adjustments_row}"
    ws[f"F{row}"] = f"=F{technical_adjustments_row}"
    ws[f"G{row}"] = f"=G{technical_adjustments_row}"
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    bottom_border(ws, row)
    row += 1

    dropdown_1_row = row
    ws[f"B{row}"] = ""
    ws[f"E{row}"] = (
        f"=SUM(E{basic_vehicle_price_row}:E{technical_adjustment_price_row})"
    )
    ws[f"F{row}"] = (
        f"=SUM(F{basic_vehicle_price_row}:F{technical_adjustment_price_row})"
    )
    ws[f"G{row}"] = (
        f"=SUM(G{basic_vehicle_price_row}:G{technical_adjustment_price_row})"
    )
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    bottom_border(ws, row)
    row += 1

    ws[f"B{row}"] = "Transportation"
    ws[f"E{row}"] = 0.0
    ws[f"F{row}"] = 0.0
    ws[f"G{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    row += 1

    special_discount_row = row
    ws[f"B{row}"] = "Special Discount"
    ws[f"E{row}"] = 0.0
    ws[f"F{row}"] = 0.0
    ws[f"G{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    bottom_border(ws, row)
    row += 1

    dropdown_2_row = row
    ws[f"B{row}"] = ""
    ws[f"E{row}"] = f"=SUM(E{dropdown_1_row}:E{special_discount_row})"
    ws[f"F{row}"] = f"=SUM(F{dropdown_1_row}:F{special_discount_row})"
    ws[f"G{row}"] = f"=SUM(G{dropdown_1_row}:G{special_discount_row})"
    set_currency_format(ws, f"E{row}")
    set_currency_format(ws, f"F{row}")
    set_currency_format(ws, f"G{row}")
    double_bottom_border(ws, row)
    row += 5

    # Dropdowns (visual + data validation)
    apply_dropdown_style(ws, f"B{dropdown_1_row}")
    apply_dropdown_style(ws, f"B{dropdown_2_row}")

    blue_fill = PatternFill(fill_type="solid", fgColor="DDEEFF")
    empty_rule = FormulaRule(formula=[f"ISBLANK(B{dropdown_1_row})"], fill=blue_fill)
    ws.conditional_formatting.add(f"B{dropdown_1_row}", empty_rule)
    empty_rule_2 = FormulaRule(formula=[f"ISBLANK(B{dropdown_2_row})"], fill=blue_fill)
    ws.conditional_formatting.add(f"B{dropdown_2_row}", empty_rule_2)

    net_price_list = "NET VEHICLE PRICE,NET VEHICLE PRICE WHS,NET VEHICLE PRICE WHS GOV"
    total_price_list = "TOTAL OFFER PRICE,TOTAL OFFER PRICE WHS,TOTAL OFFER PRICE WHS GOV"

    net_price_dv = DataValidation(type="list", formula1=f'"{net_price_list}"', allow_blank=True)
    net_price_dv.showErrorMessage = False
    total_price_dv = DataValidation(type="list", formula1=f'"{total_price_list}"', allow_blank=True)
    total_price_dv.showErrorMessage = False

    ws.add_data_validation(net_price_dv)
    ws.add_data_validation(total_price_dv)

    net_price_dv.add(ws[f"B{dropdown_1_row}"])
    total_price_dv.add(ws[f"B{dropdown_2_row}"])

    # Dropdowns B4 and A8
    department_list = "CS-20/MH,CS-20/DW,CS-20/FR"
    number_type_list = "VIN,Order Nr.,Proforma Order Nr."

    department_dv = DataValidation(type="list", formula1=f'"{department_list}"', allow_blank=True)
    department_dv.showErrorMessage = False
    number_type_dv = DataValidation(type="list", formula1=f'"{number_type_list}"', allow_blank=True)
    number_type_dv.showErrorMessage = False

    ws.add_data_validation(department_dv)
    ws.add_data_validation(number_type_dv)

    department_dv.add(ws["B3"])
    number_type_dv.add(ws["A7"])

    # Conditional formatting for B3 and A7
    b3_rule = FormulaRule(formula=["ISBLANK(B3)"], fill=blue_fill)
    ws.conditional_formatting.add("B3", b3_rule)
    a7_rule = FormulaRule(formula=["ISBLANK(A7)"], fill=blue_fill)
    ws.conditional_formatting.add("A7", a7_rule)

    # Dropdown for J3 (Countries)
    countries_names = ",".join([c["name"] for c in countries_list])
    country_dv = DataValidation(type="list", formula1=f'"{countries_names}"', allow_blank=True)
    country_dv.showErrorMessage = False
    ws.add_data_validation(country_dv)
    country_dv.add(ws["J3"])

    j3_rule = FormulaRule(formula=["ISBLANK(J3)"], fill=blue_fill)
    ws.conditional_formatting.add("J3", j3_rule)

    # Dropdown for E10 (Price column header)
    price_header_list = "Price EUR,Price USD,Price ZAR,Price NOK,Price GBP,Price WHS EUR,Price WHS USD,Price WHS ZAR,Price WHS NOK,Price WHS GBP,Price WHS GOV EUR,Price WHS GOV USD,Price WHS GOV ZAR,Price WHS GOV NOK,Price WHS GOV GBP"
    price_header_dv = DataValidation(type="list", formula1=f'"{price_header_list}"', allow_blank=True)
    price_header_dv.showErrorMessage = False
    ws.add_data_validation(price_header_dv)
    price_header_dv.add(ws["E10"])
    price_header_dv.add(ws["F10"])
    price_header_dv.add(ws["G10"])

    # Create Countries worksheet
    countries_ws = wb.create_sheet("Countries")
    countries_ws["A1"] = "Country"
    countries_ws["B1"] = "PAK"
    countries_ws["C1"] = "Client"

    for idx, country in enumerate(countries_list):
        row_idx = 2 + idx
        countries_ws[f"A{row_idx}"] = country["name"]
        countries_ws[f"B{row_idx}"] = country["pak"]
        countries_ws[f"C{row_idx}"] = country["client"]

    # =========================
    # PAGE 4 – TECHNICAL DATA
    # =========================

    page3_row = row
    ws[f"A{row}"] = "=A7"
    ws[f"A{row}"].alignment = Alignment(horizontal="left")
    ws[f"B{row}"] = "=B7"
    ws[f"B{row}"].alignment = Alignment(horizontal="left")
    ws[f"E{row}"] = "Page 3"
    ws[f"E{row}"].font = Font(name="Calibri", size=6)
    ws[f"E{row}"].alignment = Alignment(horizontal="right")

    technical_merge_rows = []
    technical_merge_heights = []

    next_page_row = page3_row

    interior_image_row = next_page_row + 29

    # =========================
    # INSERT IMAGES
    # =========================
    insert_exterior_image(ws, vehicle_data)
    insert_exterior_image(
        ws,
        vehicle_data,
        anchor=f"A{next_page_row + 1}",
        size_in=(9.44, 5.67),
    )
    # Rear exterior image 43 rows after Page 4
    insert_exterior_image(
        ws,
        vehicle_data,
        anchor=f"A{next_page_row + 43}",
        size_in=(9.44, 5.67),
        image_index=1,
    )
    insert_interior_image(
        ws,
        vehicle_data,
        anchor=f"A{interior_image_row}",
        size_in=(4.68, 2.81),
        image_index=0,
    )
    insert_interior_image(
        ws,
        vehicle_data,
        anchor=f"E{interior_image_row}",
        size_in=(4.68, 2.81),
        image_index=1,
        align_right_cell=f"E{interior_image_row}",
        right_offset_px=65,
    )

    # =========================
    # SAVE
    # =========================
    # Page breaks - only 2 breaks for 3 pages
    # Page 1: from top until 1 line before Page 2
    ws.row_breaks.append(Break(id=page2_row - 1))
    
    # Page 2: until 3 lines before Page 3
    ws.row_breaks.append(Break(id=page3_row - 3))
    
    # Set print area to columns A-G (no hidden area)
    ws.print_area = f'A1:G{interior_image_row + 61}'

    # Row heights
    for r in range(1, 11):
        ws.row_dimensions[r].height = 18
    if basic_vehicle_price_row and basic_vehicle_price_row > 11:
        for r in range(11, basic_vehicle_price_row):
            ws.row_dimensions[r].height = 16
    if basic_vehicle_price_row and dropdown_2_row:
        for r in range(basic_vehicle_price_row, dropdown_2_row + 1):
            ws.row_dimensions[r].height = 22.5
        for r in range(dropdown_2_row + 1, ws.max_row + 1):
            ws.row_dimensions[r].height = 16
    if technical_merge_rows and technical_merge_heights:
        for merge_row, height in zip(technical_merge_rows, technical_merge_heights):
            ws.row_dimensions[merge_row].height = height
    
    # Apply Calibri font to all cells in the worksheet
    for row in ws.iter_rows():
        for cell in row:
            if cell.font.name != "Calibri" or not cell.font.bold:
                # Preserve bold if already set, default size 10
                cell.font = Font(
                    name="Calibri",
                    size=cell.font.size or 10,
                    bold=cell.font.bold,
                    italic=cell.font.italic,
                    underline=cell.font.underline,
                    color=cell.font.color
                )
    
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, "BMW_Quotation_V1_2_LAYOUT_ONLY.xlsx")
    wb.save(file_path)

    return file_path
