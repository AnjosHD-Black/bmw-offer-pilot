import re
from typing import List, Dict

# ======================================================
# PRICE LINE PARSER
# ======================================================
PRICE_LINE_REGEX = re.compile(
    r"^(?P<code>[A-Z0-9]{3})\s+.+?\s+(?P<price>\d+(?:[.,]\d+)?)$"
)


def parse_priced_lines(lines: List[str]) -> Dict[str, float]:
    """
    Extrahiert Preise aus z.B.:
    '3AB Sitzheizung 100'
    '3AD M-Lenkrad 3000'
    """
    prices: Dict[str, float] = {}

    for line in lines:
        line = line.strip()
        match = PRICE_LINE_REGEX.match(line)
        if not match:
            raise ValueError(f"Invalid priced line format: {line}")

        code = match.group("code")
        price = float(match.group("price").replace(",", "."))

        prices[code] = price

    return prices


# ======================================================
# NORMALIZER (FINAL & STABLE)
# ======================================================
def normalize_vehicle_input(
    *,
    model: str,
    color: str,
    interior: str,
    all_codes: List[str],
    priced_lines: List[str],
    options_meta: Dict
) -> Dict:
    """
    Baut die finale strukturierte Fahrzeugdarstellung
    """

    priced_prices = parse_priced_lines(priced_lines)

    result = {
        "base": [],
        "standard": [],
        "optional": [],
        "security": [],
        "total_price": 0.0
    }

    # ----------------------------
    # BASE VEHICLE (inkl. TRIM)
    # ----------------------------
    base_codes = []

    for code in all_codes:
        meta = options_meta.get(code)
        if meta and meta.get("category") == "base":
            base_codes.append(code)

    for code in base_codes:
        meta = options_meta.get(code, {})

        text = (
            meta.get("text")
            or meta.get("label")
            or meta.get("description")
            or code
        )

        result["base"].append({
            "code": code,
            "text": text,
            "price": 0.0
        })

    # ----------------------------
    # ALL OTHER CODES (NICHT BASE)
    # ----------------------------
    for code in all_codes:
        if code in base_codes:
            continue

        meta = options_meta.get(code)
        if not meta:
            continue

        category = meta.get("category")

        text = (
            meta.get("text")
            or meta.get("label")
            or meta.get("description")
            or code
        )

        price = priced_prices.get(code, 0.0)

        item = {
            "code": code,
            "text": text,
            "price": price
        }

        if category == "standard":
            result["standard"].append(item)
        elif category == "optional":
            result["optional"].append(item)
        elif category == "security":
            result["security"].append(item)

        result["total_price"] += price

    return result
