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
    path = os.path.join(base_dir, "country_pak_client_g05.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_image_mappings():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "image_mappings_g05.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def insert_exterior_image(ws, vehicle_data: dict, anchor="D5", size_px=None, size_in=None, image_index=0):
    """Insert exterior image based on 475 and authority codes"""
    print("[DEBUG] insert_exterior_image called")
    
    image_mappings = load_image_mappings()
    print(f"[DEBUG] image_mappings: {image_mappings}")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "images")
    
    # Check if 475 is the exterior_color
    exterior_color = vehicle_data.get("exterior_color")
    print(f"[DEBUG] exterior_color: {exterior_color}")
    
    has_475 = False
    
    if exterior_color and isinstance(exterior_color, dict):
        has_475 = exterior_color.get("code") == "475"
        print(f"[DEBUG] dict check: has_475={has_475}")
    elif exterior_color == "475":
        has_475 = True
    
    if not has_475:
        print("[DEBUG] No 475 found, returning")
        return
    
    print("[DEBUG] 475 found, continuing...")
    
    # Check if 141 or 144 is present in security list
    security_list = vehicle_data.get("security", [])
    print(f"[DEBUG] security_list: {security_list}")
    
    has_authority = False
    
    for item in security_list:
        if isinstance(item, dict):
            code = item.get("code")
            if code in ["141", "144"]:
                has_authority = True
                break
        elif item in ["141", "144"]:
            has_authority = True
            break
    
    print(f"[DEBUG] has_authority: {has_authority}")
    
    # Determine which image set to use
    image_key = "475_authority" if has_authority else "475"
    image_files = image_mappings.get(image_key, [])
    
    print(f"[DEBUG] image_key: {image_key}, image_files: {image_files}")
    
    if not image_files:
        print("[DEBUG] No image files found")
        return
    
    # Use specified image index
    if image_index >= len(image_files):
        print(f"[DEBUG] Image index {image_index} out of range")
        return
    
    image_path = os.path.join(images_dir, image_files[image_index])
    print(f"[DEBUG] image_path: {image_path}")
    
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
        print(f"[DEBUG] Target in Excel: 2.2\" × 1.32\"")
        
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
    """Insert interior image based on interior codes (VASW/KPSW)."""
    print("[DEBUG] insert_interior_image called")

    image_mappings = load_image_mappings()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "images")

    interior_color = vehicle_data.get("interior_color")
    print(f"[DEBUG] interior_color: {interior_color}")

    code = None
    if interior_color and isinstance(interior_color, dict):
        code = interior_color.get("code")
    elif isinstance(interior_color, str):
        code = interior_color

    if code not in ["VASW", "KPSW"]:
        print("[DEBUG] No matching interior code found")
        return

    image_files = image_mappings.get(code, [])
    print(f"[DEBUG] interior image_files: {image_files}")

    if not image_files:
        print("[DEBUG] No interior image files found")
        return

    if image_index >= len(image_files):
        print(f"[DEBUG] Interior image index out of range: {image_index}")
        return

    image_path = os.path.join(images_dir, image_files[image_index])
    print(f"[DEBUG] interior image_path: {image_path}")

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
    for col in ["A", "B", "C", "D", "E", "F"]:
        ws[f"{col}{row}"].border = Border(bottom=Side(style="thin"))


def double_bottom_border(ws, row):
    for col in ["A", "B", "C", "D", "E", "F"]:
        ws[f"{col}{row}"].border = Border(bottom=Side(style="double"))


def apply_box_border(ws, start_row, end_row, start_col="A", end_col="E", style="thin"):
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

    # =========================
    # PRINT HEADER (ALL PAGES)
    # =========================
    ws.oddHeader.left.text = "LOGO 1"
    ws.oddHeader.right.text = "LOGO 2"

    # =========================
    # PAGE 1
    # =========================
    bottom_border(ws, 3)

    ws["A4"] = "Quotation"
    ws["B4"] = datetime.today().strftime("%d.%m.%Y")
    ws["E4"] = "=J5"

    ws["A5"] = "Department"
    ws["B5"] = ""

    ws["A6"] = "Type"
    ws["B6"] = "X5"

    ws["A7"] = "Protection class"
    ws["B7"] = "VR"

    ws["A8"] = ""
    ws["B8"] = ""
    ws["B8"].alignment = Alignment(horizontal="left")

    ws["A9"] = "Model Year"
    ws["B9"] = "=YEAR(H5)"
    ws["B9"].alignment = Alignment(horizontal="left")

    ws["A10"] = "Vehicle Status"
    ws["B10"] = '=IF(H5>B4,"BTO","Stock")'

    bottom_border(ws, 10)

    # New columns H, I, J (right side)
    ws["H4"] = "Prod. Date"
    ws["I4"] = "KW"
    ws["J4"] = "Country"

    ws["H5"] = ""
    ws["H5"].number_format = "DD.MM.YYYY"
    ws["I5"] = f"=WEEKNUM(H5,21)"
    ws["J5"] = ""

    ws["H7"] = "PAK"
    ws["I7"] = "Client"

    ws["H8"] = f'=IFERROR(VLOOKUP(J5,Countries!$A$2:$C$4,2,0),"")'
    ws["I8"] = f'=IFERROR(VLOOKUP(J5,Countries!$A$2:$C$4,3,0),"")'

    ws["H10"] = "8R3"
    ws["H11"] = f'=IF(COUNTIF(B:B,"8R3")>0,"OK","NOT OK")'

    # Undefinierte Codes aus der Eingabe rechts in Spalte J anzeigen.
    unknown_codes = vehicle_data.get("unknown_codes", [])
    ws["J13"] = "Undefined Option Codes"
    ws["J13"].font = Font(name="Calibri", size=10, bold=True, underline="single")
    for idx, code in enumerate(unknown_codes, start=14):
        ws[f"J{idx}"] = code
    
    # Add borders to H10 and H11
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    ws["H10"].border = thin_border
    ws["H11"].border = thin_border
    
    # Add borders to H4-J4, H5-J5, H7-I7, H8-I8
    for cell_ref in ["H4", "I4", "J4", "H5", "I5", "J5", "H7", "I7", "H8", "I8"]:
        ws[cell_ref].border = thin_border
    
    # Add conditional formatting to H11: red background if 8R3 is not present
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    red_font = Font(color="FFFFFF")
    cf_rule = FormulaRule(formula=[f'=COUNTIF(B:B,"8R3")=0'], fill=red_fill, font=red_font)
    ws.conditional_formatting.add(f'H11', cf_rule)

    ws["D11"] = "=H8"
    ws["D11"].font = Font(name="Calibri", size=8, underline="single")
    ws["D11"].alignment = Alignment(horizontal="right")
    
    ws["E11"] = "Page 1"
    ws["E11"].font = Font(name="Calibri", size=6)
    ws["E11"].alignment = Alignment(horizontal="right")

    ws["B12"] = "Option Code"
    ws["C12"] = "Description"
    ws["E12"] = "Price"
    ws["E12"].alignment = Alignment(horizontal="right")
    ws["F12"].alignment = Alignment(horizontal="right")

    underline(ws, "B12")
    underline(ws, "C12")
    underline(ws, "E12")
    underline(ws, "F12")

    row = 13

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
        row += 1

    base_vehicle_row = base_row_map.get("base_vehicle")
    exterior_color_row = base_row_map.get("exterior_color")
    interior_color_row = base_row_map.get("interior_color")
    interior_trim_row = base_row_map.get("interior_trim")

    bottom_border(ws, row - 1)

    def write_section(start_row, label, items):
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
        start_item_row = start_row
        end_item_row = start_row

        row_cursor = start_row + 1
        for item in items[1:]:
            ws[f"B{row_cursor}"] = item.get("code", "")
            center_cell(ws, f"B{row_cursor}")
            ws[f"C{row_cursor}"] = item.get("text", "")
            ws[f"E{row_cursor}"] = item.get("price", 0.0)
            set_number_format(ws, f"E{row_cursor}")
            end_item_row = row_cursor
            row_cursor += 1

        return row_cursor, start_item_row, end_item_row

    # ----- STANDARD EQUIPMENT -----
    row, _, _ = write_section(row, "Standard Equipment", vehicle_data.get("standard", []))
    row += 1

    # ----- SECURITY EQUIPMENT -----
    security_package = vehicle_data.get("security_package") or {}
    security_items = vehicle_data.get("security", [])
    security_items_start = None
    security_items_end = None

    security_package_row = row
    ws[f"A{row}"] = "Security Equipment"
    underline(ws, f"A{row}")
    ws[f"B{row}"] = security_package.get("code", "")
    center_cell(ws, f"B{row}")
    ws[f"C{row}"] = security_package.get("text", "")
    ws[f"E{row}"] = security_package.get("price", 0.0)
    set_number_format(ws, f"E{row}")
    row += 1

    security_text_lines = [
        "VR Protection",
        "Intercom System",
        "Electric Window",
        "Windscreen",
        "Fuel Tank",
        "Splinter Protection",
    ]

    for line in security_text_lines:
        ws[f"C{row}"] = line
        row += 1

    for item in security_items:
        if security_items_start is None:
            security_items_start = row
        security_items_end = row
        ws[f"B{row}"] = item.get("code", "")
        center_cell(ws, f"B{row}")
        ws[f"C{row}"] = item.get("text", "")
        ws[f"E{row}"] = item.get("price", 0.0)
        set_number_format(ws, f"E{row}")
        row += 1

    row += 2

    # =========================
    # PAGE 2
    # =========================
    ws.row_breaks.append(Break(id=row - 2))

    ws[f"A{row}"] = "=A8"
    ws[f"A{row}"].alignment = Alignment(horizontal="left")
    ws[f"B{row}"] = "=B8"
    ws[f"B{row}"].alignment = Alignment(horizontal="left")
    ws[f"E{row}"] = "Page 2"
    ws[f"E{row}"].font = Font(name="Calibri", size=6)
    ws[f"E{row}"].alignment = Alignment(horizontal="right")
    row += 2

    row, optional_items_start, optional_items_end = write_section(
        row,
        "Optional Equipment",
        vehicle_data.get("optional", [])
    )

    row += 1

    technical_adjustments_row = row
    # Add top border from A to F
    for col in ["A", "B", "C", "D", "E", "F"]:
        ws[f"{col}{row}"].border = Border(top=Side(style='thin'))
    
    ws[f"A{row}"] = "Technical Adjustments"
    underline(ws, f"A{row}")
    row += 1

    ws[f"A{row}"] = "Additions"
    underline(ws, f"A{row}")
    row += 2
    
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
    set_currency_format(ws, f"E{row}")
    row += 1

    security_package_price_row = row
    ws[f"B{row}"] = "Security Package VR6"
    if security_package_row:
        ws[f"E{row}"] = f"=E{security_package_row}"
    else:
        ws[f"E{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    row += 1

    optional_equipment_price_row = row
    ws[f"B{row}"] = "Optional Equipment"
    optional_sum_parts = [
        f"E{r}"
        for r in [exterior_color_row, interior_color_row, interior_trim_row]
        if r
    ]

    if security_items_start and security_items_end:
        optional_sum_parts.append(f"E{security_items_start}:E{security_items_end}")

    if optional_items_start and optional_items_end:
        optional_sum_parts.append(f"E{optional_items_start}:E{optional_items_end}")

    if optional_sum_parts:
        ws[f"E{row}"] = "=SUM(" + ",".join(optional_sum_parts) + ")"
    else:
        ws[f"E{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    row += 1

    technical_adjustment_price_row = row
    ws[f"B{row}"] = "Technical Adjustment"
    ws[f"E{row}"] = f"=E{technical_adjustments_row}"
    set_currency_format(ws, f"E{row}")
    bottom_border(ws, row)
    row += 1

    dropdown_1_row = row
    ws[f"B{row}"] = ""
    ws[f"E{row}"] = (
        f"=SUM(E{basic_vehicle_price_row}:E{technical_adjustment_price_row})"
    )
    set_currency_format(ws, f"E{row}")
    bottom_border(ws, row)
    row += 1

    ws[f"B{row}"] = "Transportation"
    ws[f"E{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    row += 1

    special_discount_row = row
    ws[f"B{row}"] = "Special Discount"
    ws[f"E{row}"] = 0.0
    set_currency_format(ws, f"E{row}")
    bottom_border(ws, row)
    row += 1

    dropdown_2_row = row
    ws[f"B{row}"] = ""
    ws[f"E{row}"] = f"=SUM(E{dropdown_1_row}:E{special_discount_row})"
    set_currency_format(ws, f"E{row}")
    double_bottom_border(ws, row)
    dropdown_merge_row = row + 1
    ws.merge_cells(f"A{dropdown_merge_row}:E{dropdown_merge_row}")
    ws.row_dimensions[dropdown_merge_row].height = 28.5
    ws[f"A{dropdown_merge_row}"] = "aaaaaaaaaaaaaaaaaaaa. aaaaaaaaaaaaaaaaaaaaaaaa."
    ws[f"A{dropdown_merge_row}"].font = Font(name="Calibri", size=8)
    ws[f"A{dropdown_merge_row}"].alignment = Alignment(
        horizontal="left",
        vertical="top",
        wrap_text=True,
        indent=1,
    )
    row += 4

    # Dropdowns (visual + data validation)
    apply_dropdown_style(ws, f"B{dropdown_1_row}")
    apply_dropdown_style(ws, f"B{dropdown_2_row}")

    blue_fill = PatternFill(fill_type="solid", fgColor="DDEEFF")
    empty_rule = FormulaRule(formula=[f"ISBLANK(B{dropdown_1_row})"], fill=blue_fill)
    ws.conditional_formatting.add(f"B{dropdown_1_row}", empty_rule)
    empty_rule_2 = FormulaRule(formula=[f"ISBLANK(B{dropdown_2_row})"], fill=blue_fill)
    ws.conditional_formatting.add(f"B{dropdown_2_row}", empty_rule_2)

    net_price_list = "NET VEHICLE PRICE,NET VEHICLE PRICE WHS"
    total_price_list = "TOTAL OFFER PRICE,TOTAL OFFER PRICE WHS"

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

    department_dv.add(ws["B5"])
    number_type_dv.add(ws["A8"])

    # Conditional formatting for B5 and A8
    b5_rule = FormulaRule(formula=["ISBLANK(B5)"], fill=blue_fill)
    ws.conditional_formatting.add("B5", b5_rule)
    a8_rule = FormulaRule(formula=["ISBLANK(A8)"], fill=blue_fill)
    ws.conditional_formatting.add("A8", a8_rule)

    # Dropdown for J5 (Countries)
    countries_names = ",".join([c["name"] for c in countries_list])
    country_dv = DataValidation(type="list", formula1=f'"{countries_names}"', allow_blank=True)
    country_dv.showErrorMessage = False
    ws.add_data_validation(country_dv)
    country_dv.add(ws["J5"])

    j5_rule = FormulaRule(formula=["ISBLANK(J5)"], fill=blue_fill)
    ws.conditional_formatting.add("J5", j5_rule)

    # Dropdowns for E12 and F12 (Price Currency)
    price_currency_list = "Price | EUR,Price | USD,Price | ZAR,Price | NOK,Price | GBP,Price | WHS | EUR,Price | WHS | USD,Price | WHS | ZAR,Price | WHS | NOK,Price | WHS | GBP"
    price_currency_dv_e12 = DataValidation(type="list", formula1=f'"{price_currency_list}"', allow_blank=True)
    price_currency_dv_e12.showErrorMessage = False
    price_currency_dv_f12 = DataValidation(type="list", formula1=f'"{price_currency_list}"', allow_blank=True)
    price_currency_dv_f12.showErrorMessage = False
    
    ws.add_data_validation(price_currency_dv_e12)
    ws.add_data_validation(price_currency_dv_f12)
    
    price_currency_dv_e12.add(ws["E12"])
    price_currency_dv_f12.add(ws["F12"])

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
    ws.row_breaks.append(Break(id=row - 2))

    ws[f"A{row}"] = "=A8"
    ws[f"A{row}"].alignment = Alignment(horizontal="left")
    ws[f"B{row}"] = "=B8"
    ws[f"B{row}"].alignment = Alignment(horizontal="left")
    ws[f"E{row}"] = "Page 3"
    ws[f"E{row}"].font = Font(name="Calibri", size=6)
    ws[f"E{row}"].alignment = Alignment(horizontal="right")
    row += 2

    ws[f"A{row}"] = "Technical Data"
    underline(ws, f"A{row}")
    row += 1

    technical_box_start_row = row

    # Technical data with structured columns
    technical_data = [
        {"A": "", "B": "", "C": "", "D": ""},  # Empty row
        {"A": "Weight", "B": "", "C": "", "D": "", "bold": True},
        {"A": "Unladen DIN", "B": "(without Driver)", "C": "kg", "D": "3"},
        {"A": "Unladen EU", "B": "", "C": "kg", "D": "3"},
        {"A": "Gross vehicle weight", "B": "", "C": "kg", "D": "3"},
        {"A": "", "B": "", "C": "", "D": ""},  # Empty row
        {"A": "Engine¹'²", "B": "", "C": "", "D": "", "bold": True},
        {"A": "Cylinders/Valves", "B": "", "C": "", "D": "7/5"},
        {"A": "Capacity", "B": "", "C": "cc³", "D": "4"},
        {"A": "Output/Engine Speed", "B": "", "C": "kW(hp)/rpm", "D": "3"},
        {"A": "Engine Torque", "B": "", "C": "Nm", "D": "7"},
        {"A": "", "B": "", "C": "", "D": ""},  # Empty row
        {"A": "Performance", "B": "", "C": "", "D": "", "bold": True},
        {"A": "Top Speed³", "B": "", "C": "km/h", "D": "2"},
        {"A": "Acceleration 0-100 km/h", "B": "", "C": "s", "D": "5"},
        {"A": "", "B": "", "C": "", "D": ""},  # Empty row
        {"A": "Fuel Consumption", "B": "", "C": "", "D": "", "bold": True},
        {"A": "Combined", "B": "", "C": "l/100 km", "D": "1"},
        {"A": "CO2 emissions", "B": "", "C": "g/km", "D": "2"},
    ]

    for item in technical_data:
        if not item["A"] and not item["B"] and not item["C"] and not item["D"]:
            # Empty row
            row += 1
            continue
        
        ws[f"A{row}"] = item["A"]
        ws[f"B{row}"] = item["B"]
        ws[f"C{row}"] = item["C"]
        ws[f"D{row}"] = item["D"]
        
        if item.get("bold"):
            ws[f"A{row}"].font = Font(bold=True)
        
        row += 1

    empty_start_row = row
    merge_rows = [empty_start_row + 2, empty_start_row + 3, empty_start_row + 4, empty_start_row + 5]
    merge_heights = [43.5, 57.0, 22.0, 22.0]
    technical_merge_rows = merge_rows
    technical_merge_heights = merge_heights
    for merge_row, height in zip(merge_rows, merge_heights):
        ws.row_dimensions[merge_row].height = height
    for merge_row in merge_rows:
        ws.merge_cells(start_row=merge_row, start_column=1, end_row=merge_row, end_column=5)
    ws[f"A{merge_rows[0]}"] = "1 aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa. aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa. aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa."
    ws[f"A{merge_rows[1]}"] = "2 aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaa aaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaa aaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaa aaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa."
    ws[f"A{merge_rows[2]}"] = "aaaaaaaaaaaaaaaaaaaaaaaaa."
    ws[f"A{merge_rows[3]}"] = "3 aa"
    for merge_row in merge_rows:
        ws[f"A{merge_row}"].font = Font(name="Calibri", size=8)
        ws[f"A{merge_row}"].alignment = Alignment(
            horizontal="left",
            vertical="top",
            wrap_text=True,
            indent=1,
        )

    technical_box_end_row = row - 1 + 6
    apply_box_border(ws, technical_box_start_row, technical_box_end_row, "A", "E", "thin")

    next_page_row = technical_box_end_row + 3
    ws[f"A{next_page_row}"] = "=A8"
    ws[f"A{next_page_row}"].alignment = Alignment(horizontal="left")
    ws[f"B{next_page_row}"] = "=B8"
    ws[f"B{next_page_row}"].alignment = Alignment(horizontal="left")
    ws[f"E{next_page_row}"] = "Page 4"
    ws[f"E{next_page_row}"].font = Font(name="Calibri", size=6)
    ws[f"E{next_page_row}"].alignment = Alignment(horizontal="right")

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
    # Add page break before Page 4 (2 rows before)
    ws.row_breaks.append(Break(id=next_page_row - 2))
    
    # Set print area to columns A-E only, extended to fit all images on page 4
    ws.print_area = f'A1:E{interior_image_row + 61}'

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
    if dropdown_merge_row:
        ws.row_dimensions[dropdown_merge_row].height = 28.5
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
